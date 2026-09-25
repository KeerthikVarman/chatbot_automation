"""
Conversation State Persistence Manager.

Manages multi-turn conversation states in-memory per conversation_id.
Executes LangGraph workflow steps and updates state safely.
"""

from typing import Dict, Any, Optional
from models import WorkflowState
from agent import workflow_graph


class StateManager:
    def __init__(self):
        self._store: Dict[str, WorkflowState] = {}

    def get_state(self, conversation_id: str) -> Optional[WorkflowState]:
        return self._store.get(conversation_id)

    def get_or_create_state(self, conversation_id: str, initial_user_message: str) -> WorkflowState:
        if conversation_id not in self._store:
            self._store[conversation_id] = WorkflowState(
                conversation_id=conversation_id,
                user_request=initial_user_message,
                workflow_type=None,
                required_information=[],
                collected_information={},
                missing_information=[],
                ambiguities=[],
                current_question=None,
                conversation_history=[],
                workflow_ready=False,
                generated_workflow=None
            )
        return self._store[conversation_id]

    def reset_state(self, conversation_id: str) -> bool:
        if conversation_id in self._store:
            del self._store[conversation_id]
            return True
        return False

    def process_message(self, conversation_id: str, message: str) -> WorkflowState:
        """
        Processes a user message for a conversation session.
        Appends message to history, runs LangGraph agent, and saves updated state.
        """
        state = self.get_or_create_state(conversation_id, initial_user_message=message)

        # Update initial user request if this is the first turn
        if not state.get("user_request"):
            state["user_request"] = message

        # Append user message to history
        history = list(state.get("conversation_history", []))
        history.append({"role": "user", "content": message})
        state["conversation_history"] = history

        # Execute LangGraph graph execution turn
        updated_state = workflow_graph.invoke(state)

        # Update internal session store
        self._store[conversation_id] = updated_state
        return updated_state


# Global state manager instance
state_manager = StateManager()
