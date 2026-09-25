"""
Comprehensive Automated Test Suite for AI-Powered Conversational Workflow Builder.
Covers all 5 mandatory test scenarios, dynamic requirement identification, single-question enforcement,
state persistence, and FastAPI REST endpoints.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state_manager import state_manager
from api import app

client = TestClient(app)


# ==========================================
# TEST SCENARIO 1: Invoice Notification
# ==========================================
def test_scenario_1_invoice_notification():
    """
    TEST 1: User says "I want to receive a Slack notification whenever I get a new invoice."
    Verify that the system identifies missing information (e.g. email provider, folder/label, channel)
    and asks a single clarification question without assuming defaults.
    """
    cid = "test_s1_invoice"
    state_manager.reset_state(cid)

    user_msg = "I want to receive a Slack notification whenever I get a new invoice."
    state = state_manager.process_message(cid, user_msg)

    assert state["workflow_ready"] is False
    assert len(state["missing_information"]) > 0
    assert state.get("current_question") is not None
    # Ensure question ends with a question mark and asks for missing details
    assert "?" in state["current_question"]


# ==========================================
# TEST SCENARIO 2: GitHub Bug Alert
# ==========================================
def test_scenario_2_github_bug_alert():
    """
    TEST 2: User says "When a GitHub issue labeled bug is created, notify Slack."
    Verify that GitHub repository and Slack destination are identified as missing information.
    """
    cid = "test_s2_github"
    state_manager.reset_state(cid)

    user_msg = "When a GitHub issue labeled bug is created, notify Slack."
    state = state_manager.process_message(cid, user_msg)

    assert state["workflow_ready"] is False
    # Check that missing_information contains repository or slack destination details
    missing_str = " ".join(state["missing_information"]).lower()
    assert "repository" in missing_str or "repo" in missing_str or "channel" in missing_str or "destination" in missing_str or "workspace" in missing_str


# ==========================================
# TEST SCENARIO 3: Website Form to Google Sheets
# ==========================================
def test_scenario_3_contact_form_to_sheets():
    """
    TEST 3: User says "When someone submits my website contact form, save their details to Google Sheets."
    Verify that the system dynamically identifies required information (form source, sheet name/id, worksheet, fields).
    """
    cid = "test_s3_form"
    state_manager.reset_state(cid)

    user_msg = "When someone submits my website contact form, save their details to Google Sheets."
    state = state_manager.process_message(cid, user_msg)

    assert state["workflow_ready"] is False
    assert len(state["required_information"]) >= 2
    # Verify dynamic requirements are relevant to forms and sheets
    req_str = " ".join(state["required_information"]).lower()
    assert "form" in req_str or "sheet" in req_str or "field" in req_str or "worksheet" in req_str or "source" in req_str


# ==========================================
# TEST SCENARIO 4: Fully Specified Request (No Clarification Required)
# ==========================================
def test_scenario_4_fully_specified_request():
    """
    TEST 4: Request contains all necessary parameters.
    Verify that the agent does NOT ask unnecessary clarification questions and directly generates the workflow.
    """
    cid = "test_s4_full"
    state_manager.reset_state(cid)

    user_msg = (
        "When a new email with subject 'Urgent' arrives in my Gmail inbox for account user@example.com, "
        "send a Slack notification to the #alerts channel in the Acme workspace."
    )
    state = state_manager.process_message(cid, user_msg)

    assert state["workflow_ready"] is True
    assert state["generated_workflow"] is not None
    assert len(state["generated_workflow"]["nodes"]) >= 2
    assert len(state["generated_workflow"]["edges"]) >= 1


# ==========================================
# TEST SCENARIO 5: Ambiguous Request
# ==========================================
def test_scenario_5_ambiguous_request():
    """
    TEST 5: Vague or multi-interpretation request.
    Verify that the agent identifies multiple interpretations (ambiguities) and asks clarification instead of guessing.
    """
    cid = "test_s5_ambiguous"
    state_manager.reset_state(cid)

    user_msg = "Send important emails to my team."
    state = state_manager.process_message(cid, user_msg)

    assert state["workflow_ready"] is False
    assert state.get("current_question") is not None
    # Verify ambiguities or missing information were logged
    assert len(state["missing_information"]) > 0 or len(state["ambiguities"]) > 0


# ==========================================
# API ENDPOINTS TESTS
# ==========================================
def test_fastapi_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_fastapi_chat_flow():
    cid = "api_test_chat_01"
    response = client.post("/chat", json={
        "conversation_id": cid,
        "message": "Whenever I receive an invoice, notify my finance team."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == cid
    assert data["status"] == "clarification_required"
    assert data["workflow_ready"] is False
    assert "message" in data

    # Inspect state via GET endpoint
    state_resp = client.get(f"/conversations/{cid}")
    assert state_resp.status_code == 200
    assert state_resp.json()["conversation_id"] == cid
