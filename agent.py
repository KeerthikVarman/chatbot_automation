"""
LangGraph Workflow Builder Agent implementation.

Orchestrates state transitions:
START -> analyze_request -> check_missing_information -> (clarification | generate_workflow) -> END
"""

import json
from typing import Any, Dict, List, Literal

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from config import get_llm, invoke_structured_with_fallback
from models import (
    WorkflowState,
    RequirementAnalysis,
    GeneratedWorkflow,
)
from tools import get_available_tools_prompt_summary


# ==========================================
# System Prompts
# ==========================================

REQUIREMENT_ANALYSIS_SYSTEM_PROMPT = """
You are an expert AI Workflow Architect similar to n8n's workflow builder assistant.
Your task is to analyze natural language automation requests, determine what information is needed to build a structured workflow representation, and track collected vs missing details.

IMPORTANT RULES & INSTRUCTIONS:
1. DYNAMIC REQUIREMENT IDENTIFICATION:
   - Do NOT hard-code a fixed list of parameters for every request.
   - Dynamically identify required parameters based on the specific user request type.
   - Examples:
     * Email Invoice Alert: required parameters might be email_platform, invoice_filter_or_label, notification_platform, notification_channel_or_recipient.
     * GitHub Issue Alert: required parameters might be github_repository, issue_label, notification_platform, target_channel.
     * Web Form to Sheet: required parameters might be form_source, google_sheet_name, worksheet_name, fields_to_save.

2. ABSOLUTE NO ASSUMPTIONS & DYNAMIC PLATFORM CLARIFICATION:
   - Do NOT assume or default to any specific service (e.g., Slack, Gmail, Google Sheets) unless explicitly mentioned in the user prompt.
   - If the user request does not specify the target platform (e.g. "send an alert" or "notify me"), identify `notification_platform` as a missing parameter.
   - Formulate `next_question` to ask which target platform and destination channel/recipient the user wants to use (e.g., "Which platform (e.g., Slack, Email, Discord, Teams) and destination channel/recipient should receive the notification?").
   - If a parameter is missing, add it to `missing_information`.

3. FULLY SPECIFIED REQUEST HANDLING:
   - If the user's initial prompt ALREADY contains all core parameters for both trigger and action (e.g., email account, folder/subject, notification service, workspace, channel), do NOT invent optional missing parameters.
   - Set `missing_information` = [], `ambiguities` = [], `clarification_required` = False, and `next_question` = None.

4. STRICT NON-DUPLICATION OF QUESTIONS:
   - Check `collected_information` carefully. NEVER ask for a parameter that is already present in `collected_information`.
   - Merge updated information provided by the user into `collected_information`.

5. AMBIGUITY DETECTION:
   - If the request has vague terms (e.g., "Send important emails to my team" -> ambiguous email provider, ambiguous definition of "important", ambiguous recipient team), list these in `ambiguities`.

6. ONE CLARIFICATION QUESTION AT A TIME:
   - If `missing_information` or `ambiguities` exist, set `clarification_required` = True.
   - Formulate `next_question` to ask ONLY ONE SINGLE clarification question covering the top missing item or ambiguity.
   - NEVER ask multiple questions at once (e.g., do NOT ask "What email platform, label, and channel?").

Available Abstract Tools for Reference:
{available_tools}
"""

WORKFLOW_GENERATION_SYSTEM_PROMPT = """
You are an expert AI Workflow Generator.
Given a user's original request and all collected mandatory parameters, generate a complete structured workflow representation using nodes and edges.

RULES:
1. Do NOT execute external workflows or make real API calls.
2. Construct a logical DAG of workflow nodes (triggers, actions, filters, transformers) with proper configuration.
3. Node `id` should be descriptive (e.g. 'gmail_trigger', 'slack_notification', 'github_issue_trigger').
4. Include all collected parameters in the node `config` dicts.
5. Create edges linking the nodes sequentially from trigger to filter/action.

Available Abstract Tools:
{available_tools}
"""


# ==========================================
# Graph Node Functions
# ==========================================

def analyze_request_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node 1: Analyzes user request, updates collected parameters, and checks missing details.
    """
    system_prompt = REQUIREMENT_ANALYSIS_SYSTEM_PROMPT.format(
        available_tools=get_available_tools_prompt_summary()
    )

    history_str = ""
    for msg in state.get("conversation_history", []):
        history_str += f"{msg['role'].upper()}: {msg['content']}\n"

    prev_collected = state.get("collected_information", {})
    collected_str = json.dumps(prev_collected, indent=2)

    user_prompt = f"""
ORIGINAL USER REQUEST:
{state.get('user_request', '')}

CONVERSATION HISTORY SO FAR:
{history_str}

PREVIOUSLY COLLECTED INFORMATION:
{collected_str}

LATEST USER MESSAGE:
{state.get('conversation_history', [{}])[-1].get('content', '') if state.get('conversation_history') else state.get('user_request', '')}

Analyze the complete context:
1. Determine the overall workflow_type.
2. Determine dynamic required_information for this workflow type.
3. Update collected_information by incorporating any new details supplied in the latest message alongside previously collected details.
4. Identify missing_information and ambiguities.
5. Determine if clarification_required is True.
6. If clarification_required is True, set next_question to ask EXACTLY ONE question for the next missing parameter.
"""

    analysis: RequirementAnalysis = invoke_structured_with_fallback(
        schema_cls=RequirementAnalysis,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0
    )

    # Convert CollectedParameter list to Dict for state storage
    new_collected_dict = dict(prev_collected)
    for item in analysis.collected_information:
        new_collected_dict[item.key] = item.value

    # Respect LLM clarification decision and detect fully specified requests
    core_keys = set(new_collected_dict.keys())
    has_trigger_and_action = (
        ("email_account" in core_keys or "subject_filter" in core_keys or "github_repository" in core_keys or "form_source" in core_keys) and
        ("channel" in core_keys or "workspace" in core_keys or "google_sheet_name" in core_keys)
    )

    if not analysis.clarification_required or has_trigger_and_action:
        analysis.missing_information = []
        analysis.ambiguities = []
        analysis.clarification_required = False
        workflow_ready = True
    else:
        has_missing = len(analysis.missing_information) > 0 or len(analysis.ambiguities) > 0
        workflow_ready = not has_missing

    return {
        "workflow_type": analysis.workflow_type,
        "required_information": analysis.required_information,
        "collected_information": new_collected_dict,
        "missing_information": analysis.missing_information,
        "ambiguities": analysis.ambiguities,
        "current_question": analysis.next_question if not workflow_ready else None,
        "workflow_ready": workflow_ready
    }


def clarification_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node 2: Asks single clarification question and appends it to conversation history.
    """
    question = state.get("current_question")

    if not question:
        missing = state.get("missing_information", [])
        ambiguities = state.get("ambiguities", [])
        if missing:
            question = f"Could you please specify the {missing[0].replace('_', ' ')}?"
        elif ambiguities:
            question = f"Could you please clarify: {ambiguities[0]}?"
        else:
            question = "Could you provide more details about your workflow requirements?"

    history = list(state.get("conversation_history", []))
    if not history or history[-1].get("content") != question:
        history.append({"role": "assistant", "content": question})

    return {
        "current_question": question,
        "conversation_history": history,
        "workflow_ready": False
    }


def generate_workflow_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node 3: Generates final structured workflow representation once all info is collected.
    """
    system_prompt = WORKFLOW_GENERATION_SYSTEM_PROMPT.format(
        available_tools=get_available_tools_prompt_summary()
    )

    user_prompt = f"""
ORIGINAL USER REQUEST:
{state.get('user_request', '')}

WORKFLOW TYPE:
{state.get('workflow_type', 'General Automation')}

COLLECTED INFORMATION:
{json.dumps(state.get('collected_information', {}), indent=2)}

Generate a complete, structured GeneratedWorkflow representation with nodes and edges.
"""

    workflow: GeneratedWorkflow = invoke_structured_with_fallback(
        schema_cls=GeneratedWorkflow,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0
    )

    workflow_dict = workflow.model_dump()
    final_msg = f"I have collected all required information and generated the workflow: '{workflow.name}'."

    history = list(state.get("conversation_history", []))
    history.append({"role": "assistant", "content": final_msg})

    return {
        "generated_workflow": workflow_dict,
        "workflow_ready": True,
        "current_question": None,
        "conversation_history": history
    }


def check_missing_information_condition(state: WorkflowState) -> Literal["clarification", "generate_workflow"]:
    """
    Conditional Edge: Checks whether missing information remains or workflow is ready to generate.
    """
    if state.get("workflow_ready", False):
        return "generate_workflow"
    return "clarification"


# ==========================================
# LangGraph Builder
# ==========================================

def create_workflow_graph():
    """
    Constructs and compiles the LangGraph State Graph.
    """
    builder = StateGraph(WorkflowState)

    builder.add_node("analyze_request", analyze_request_node)
    builder.add_node("clarification", clarification_node)
    builder.add_node("generate_workflow", generate_workflow_node)

    builder.add_edge(START, "analyze_request")
    builder.add_conditional_edges(
        "analyze_request",
        check_missing_information_condition,
        {
            "clarification": "clarification",
            "generate_workflow": "generate_workflow"
        }
    )
    builder.add_edge("clarification", END)
    builder.add_edge("generate_workflow", END)

    return builder.compile()


# Global graph instance
workflow_graph = create_workflow_graph()
