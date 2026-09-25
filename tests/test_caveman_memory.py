"""
Automated unit & integration tests for Caveman Memory Context Reduction & Workflow Builder.

Tests:
1. Short conversation context reduction
2. Long conversation context reduction
3. Multiple clarification turns
4. Latest user message preservation
5. Structured collected_information preservation
6. Caveman failure -> original history fallback
7. Fully specified workflow execution
8. Workflow requiring multiple clarification questions
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from memory.caveman_memory import reduce_conversation_context, compress_turn_content, count_tokens
from agent import workflow_graph, create_workflow_graph


def test_1_short_conversation():
    """Test 1: Short conversation (1 turn) should return untouched."""
    history = [{"role": "user", "content": "I want an automation for my Gmail account user@example.com."}]
    reduced, metrics = reduce_conversation_context(history)
    
    assert len(reduced) == 1
    assert reduced[0]["content"] == history[0]["content"]
    assert metrics["original_tokens"] == metrics["reduced_tokens"]
    assert metrics["reduction_percentage"] == 0.0


def test_2_long_conversation():
    """Test 2: Long conversation context reduction achieves positive token savings."""
    history = [
        {"role": "user", "content": "Hello, I would like to create an automated workflow for my company email."}
        for _ in range(5)
    ]
    history.append({"role": "user", "content": "Send a Slack message to #alerts channel in Acme workspace."})
    
    reduced, metrics = reduce_conversation_context(history)
    
    assert len(reduced) == len(history)
    assert metrics["tokens_saved"] > 0
    assert metrics["reduction_percentage"] > 0
    assert metrics["original_tokens"] > metrics["reduced_tokens"]


def test_3_multiple_clarification_turns():
    """Test 3: Multiple clarification turns are compressed while maintaining roles."""
    history = [
        {"role": "user", "content": "I want an automation for my Gmail."},
        {"role": "assistant", "content": "Could you please specify which notification platform should receive the alert?"},
        {"role": "user", "content": "Please send it to Slack."},
        {"role": "assistant", "content": "Could you please specify the Slack channel or workspace?"},
        {"role": "user", "content": "#alerts channel in Acme workspace."}
    ]
    reduced, metrics = reduce_conversation_context(history)
    
    assert len(reduced) == 5
    assert reduced[-1]["content"] == "#alerts channel in Acme workspace."  # Latest preserved
    assert metrics["reduction_percentage"] > 0.0


def test_4_latest_user_message_preservation():
    """Test 4: Latest user message is preserved exactly without any modification."""
    history = [
        {"role": "user", "content": "Hello! Could you please help me build an email automation?"},
        {"role": "assistant", "content": "Sure, which platform?"},
        {"role": "user", "content": "Slack channel #finance with account admin@company.com"}
    ]
    reduced, metrics = reduce_conversation_context(history)
    
    # Verify latest message exact equality
    assert reduced[-1]["content"] == "Slack channel #finance with account admin@company.com"
    assert reduced[-1]["role"] == "user"


from agent import analyze_request_node, workflow_graph, create_workflow_graph

def test_5_structured_collected_information_preservation():
    """Test 5: Structured collected_information entries are preserved across state transitions."""
    initial_state = {
        "user_request": "When a new invoice email arrives, notify Slack.",
        "collected_information": {
            "email_account": "billing@example.com",
            "notification_platform": "Slack",
            "channel": "#finance"
        },
        "conversation_history": [
            {"role": "user", "content": "When a new invoice email arrives, notify Slack."},
            {"role": "assistant", "content": "Which email account?"},
            {"role": "user", "content": "billing@example.com"}
        ]
    }
    
    result = analyze_request_node(initial_state)
    collected = result.get("collected_information", {})
    
    assert collected.get("email_account") == "billing@example.com"
    assert collected.get("notification_platform") == "Slack"
    assert collected.get("channel") == "#finance"


def test_6_caveman_failure_fallback(monkeypatch):
    """Test 6: Simulated Caveman exception falls back to original history safely."""
    history = [
        {"role": "user", "content": "Trigger on new email."},
        {"role": "user", "content": "Send to Slack channel #general."}
    ]
    
    # Force an error in count_tokens to test fallback exception handling
    def mock_count_tokens_error(text):
        raise ValueError("Simulated tokenizer failure")
    
    monkeypatch.setattr("memory.caveman_memory.count_tokens", mock_count_tokens_error)
    
    reduced, metrics = reduce_conversation_context(history)
    
    # Should safely return original history list
    assert len(reduced) == 2
    assert reduced == history
    assert "error" in metrics or metrics["reduction_percentage"] == 0.0


def test_7_fully_specified_workflow():
    """Test 7: Fully specified request generates workflow in 1 turn without clarification."""
    full_prompt = (
        "When a new email with subject 'Urgent' arrives in my Gmail inbox for account user@example.com, "
        "send a Slack notification to the #alerts channel in the Acme workspace."
    )
    initial_state = {
        "user_request": full_prompt,
        "conversation_history": [{"role": "user", "content": full_prompt}],
        "collected_information": {}
    }
    
    result = workflow_graph.invoke(initial_state)
    
    assert result.get("workflow_ready") is True
    assert result.get("generated_workflow") is not None
    assert "nodes" in result["generated_workflow"]
    assert "edges" in result["generated_workflow"]


def test_8_multiple_clarification_questions_loop():
    """Test 8: System handles multi-turn clarification questions step-by-step."""
    app = create_workflow_graph()
    
    # Turn 1: Partial prompt
    state1 = {
        "user_request": "Send an alert when an email arrives.",
        "conversation_history": [{"role": "user", "content": "Send an alert when an email arrives."}],
        "collected_information": {}
    }
    res1 = app.invoke(state1)
    
    assert res1.get("workflow_ready") is False
    assert res1.get("current_question") is not None
    
    # Turn 2: User provides email details
    hist2 = list(res1.get("conversation_history", []))
    hist2.append({"role": "user", "content": "My email account is user@example.com and subject is Invoice."})
    
    state2 = {
        "user_request": state1["user_request"],
        "conversation_history": hist2,
        "collected_information": res1.get("collected_information", {})
    }
    res2 = app.invoke(state2)
    
    # Turn 3: User specifies platform
    hist3 = list(res2.get("conversation_history", []))
    hist3.append({"role": "user", "content": "Send a Slack message to #finance channel in Acme workspace."})
    
    state3 = {
        "user_request": state1["user_request"],
        "conversation_history": hist3,
        "collected_information": res2.get("collected_information", {})
    }
    res3 = app.invoke(state3)
    
    assert res3.get("workflow_ready") is True
    assert res3.get("generated_workflow") is not None
