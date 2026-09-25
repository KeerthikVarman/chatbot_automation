from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# ==========================================
# 1. Pydantic Models for LLM Structured Output
# ==========================================

class CollectedParameter(BaseModel):
    """Key-value pair representation of a single collected parameter."""
    key: str = Field(description="Parameter key/name, e.g., 'email_provider'")
    value: str = Field(description="Parameter value, e.g., 'Gmail'")


class RequirementAnalysis(BaseModel):
    """
    Structured response from LLM analyzing user request and current state.
    """
    workflow_type: str = Field(
        ...,
        description="The category or type of workflow requested (e.g., 'Email Notification', 'GitHub Issue Tracker', 'Form to Sheet Ingestion')."
    )
    required_information: List[str] = Field(
        ...,
        description="Dynamically determined list of specific parameters needed to construct this workflow."
    )
    collected_information: List[CollectedParameter] = Field(
        default_factory=list,
        description="List of key-value parameters collected from user input so far."
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="List of parameters still required but not yet specified by the user."
    )
    ambiguities: List[str] = Field(
        default_factory=list,
        description="List of ambiguous requirements or multiple possible interpretations in the request."
    )
    clarification_required: bool = Field(
        ...,
        description="True if missing parameters or ambiguities remain, False if all information is present."
    )
    next_question: Optional[str] = Field(
        default=None,
        description="The SINGLE best clarification question to ask the user next. Must ask ONLY ONE question."
    )


# ==========================================
# 2. Pydantic Models for Workflow Representation
# ==========================================

class WorkflowNode(BaseModel):
    """
    Represents a single node in the workflow graph.
    """
    id: str = Field(..., description="Unique node identifier, e.g., 'gmail_trigger'")
    type: str = Field(..., description="Node category, e.g., 'trigger', 'action', 'filter', 'transform'")
    name: str = Field(..., description="Human-readable node display name")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration parameters collected for this node")


class WorkflowEdge(BaseModel):
    """
    Represents a directional connection between two workflow nodes.
    """
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")


class GeneratedWorkflow(BaseModel):
    """
    Complete structured representation of a generated workflow.
    """
    name: str = Field(..., description="Workflow title")
    description: str = Field(..., description="Detailed description of what the workflow performs")
    nodes: List[WorkflowNode] = Field(..., description="List of component nodes")
    edges: List[WorkflowEdge] = Field(..., description="List of connections between nodes")


# ==========================================
# 3. LangGraph Workflow State Model
# ==========================================

class WorkflowState(TypedDict):
    """
    Generic conversation and workflow planning state tracked by LangGraph.
    """
    conversation_id: str
    user_request: str
    workflow_type: Optional[str]
    required_information: List[str]
    collected_information: Dict[str, Any]
    missing_information: List[str]
    ambiguities: List[str]
    current_question: Optional[str]
    conversation_history: List[Dict[str, str]]
    workflow_ready: bool
    generated_workflow: Optional[Dict[str, Any]]


# ==========================================
# 4. FastAPI Request / Response Models
# ==========================================

class ChatRequest(BaseModel):
    conversation_id: str = Field(..., description="Unique identifier for the conversation session")
    message: str = Field(..., description="User's natural language input message")


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    status: str = Field(..., description="'clarification_required' or 'workflow_ready'")
    workflow_ready: bool
    workflow: Optional[Dict[str, Any]] = None
    collected_information: Dict[str, Any] = Field(default_factory=dict)
    missing_information: List[str] = Field(default_factory=list)
    ambiguities: List[str] = Field(default_factory=list)
