"""
FastAPI HTTP API Server for Conversational Workflow Builder.
Exposes REST endpoints for chatting with the workflow planning agent,
inspecting state, and managing sessions.
"""

import os
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from models import ChatRequest, ChatResponse
from state_manager import state_manager


app = FastAPI(
    title="AI-Powered Conversational Workflow Builder API",
    description="REST API for natural language workflow planning, interactive clarification, and structured workflow generation.",
    version="1.0.0"
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static interactive Web Application
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "workflow_builder_api"}


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    """
    Primary chat endpoint for conversational workflow building.
    Processes user input, updates conversation state via LangGraph, and returns
    either a single clarification question or the generated workflow.
    """
    if not request.conversation_id or not request.conversation_id.strip():
        raise HTTPException(status_code=400, detail="conversation_id cannot be empty")
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    try:
        updated_state = state_manager.process_message(
            conversation_id=request.conversation_id.strip(),
            message=request.message.strip()
        )

        workflow_ready = updated_state.get("workflow_ready", False)
        status_str = "workflow_ready" if workflow_ready else "clarification_required"

        if workflow_ready:
            workflow = updated_state.get("generated_workflow")
            workflow_name = workflow.get("name", "Custom Workflow") if workflow else "Workflow"
            msg = f"I have collected all required information and generated the workflow: '{workflow_name}'."
        else:
            msg = updated_state.get("current_question") or "Could you please provide more details?"

        return ChatResponse(
            conversation_id=request.conversation_id,
            message=msg,
            status=status_str,
            workflow_ready=workflow_ready,
            workflow=updated_state.get("generated_workflow") if workflow_ready else None,
            collected_information=updated_state.get("collected_information", {}),
            missing_information=updated_state.get("missing_information", []),
            ambiguities=updated_state.get("ambiguities", [])
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}"
        )


@app.get("/conversations/{conversation_id}", tags=["State Management"])
async def get_conversation_state(conversation_id: str):
    """Retrieves current conversation state for debugging and visual inspection."""
    state = state_manager.get_state(conversation_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"No conversation found for ID: {conversation_id}")
    return state


@app.post("/conversations/{conversation_id}/reset", tags=["State Management"])
async def reset_conversation_state(conversation_id: str):
    """Resets conversation state for a given conversation_id."""
    success = state_manager.reset_state(conversation_id)
    return {"conversation_id": conversation_id, "reset": success}
