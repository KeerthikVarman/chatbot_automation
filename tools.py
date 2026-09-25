"""
Abstract / Mock Workflow Components Registry.

These tools serve purely as metadata and schema descriptors for constructing 
structured workflow representations. They DO NOT execute external APIs or services.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ToolMetadata(BaseModel):
    name: str
    type: str  # 'trigger', 'action', 'filter', 'transform'
    description: str
    supported_params: List[str]


# Registry of available abstract tools for workflow generation
MOCK_TOOLS_REGISTRY: Dict[str, ToolMetadata] = {
    "GmailTriggerTool": ToolMetadata(
        name="Gmail Trigger",
        type="trigger",
        description="Triggers workflow when a new email matching criteria arrives in Gmail.",
        supported_params=["email_account", "folder_or_label", "subject_filter", "sender_filter"]
    ),
    "OutlookTriggerTool": ToolMetadata(
        name="Outlook Trigger",
        type="trigger",
        description="Triggers workflow when a new email arrives in Outlook.",
        supported_params=["email_account", "folder_or_label", "subject_filter"]
    ),
    "SlackNotificationTool": ToolMetadata(
        name="Slack Notification Action",
        type="action",
        description="Sends a notification message to a specified Slack channel or workspace.",
        supported_params=["workspace", "channel", "message_template", "recipient"]
    ),
    "EmailNotificationActionTool": ToolMetadata(
        name="Email Notification Action",
        type="action",
        description="Sends an email notification to specified recipient addresses.",
        supported_params=["recipient_email", "subject", "message_body"]
    ),
    "TeamsNotificationActionTool": ToolMetadata(
        name="Microsoft Teams Action",
        type="action",
        description="Sends a message or alert to a Microsoft Teams channel.",
        supported_params=["team_name", "channel_name", "message_template"]
    ),
    "GenericNotificationActionTool": ToolMetadata(
        name="Generic Notification Dispatcher",
        type="action",
        description="Dispatches a notification to any user-specified messaging platform.",
        supported_params=["notification_platform", "destination_channel_or_recipient", "message"]
    ),
    "GitHubTriggerTool": ToolMetadata(
        name="GitHub Issue Trigger",
        type="trigger",
        description="Triggers workflow when an issue or PR is created/updated in GitHub.",
        supported_params=["repository", "label_filter", "event_type"]
    ),
    "GoogleSheetsActionTool": ToolMetadata(
        name="Google Sheets Row Action",
        type="action",
        description="Appends or updates a row in a specified Google Sheet.",
        supported_params=["spreadsheet_name_or_id", "worksheet_name", "columns_mapping"]
    ),
    "WebhookTriggerTool": ToolMetadata(
        name="Webhook Trigger",
        type="trigger",
        description="Triggers workflow on incoming HTTP POST payload (e.g. website form).",
        supported_params=["endpoint_url", "form_source", "expected_fields"]
    ),
    "FilterNodeTool": ToolMetadata(
        name="Data Filter Node",
        type="filter",
        description="Filters items based on specified conditions before downstream processing.",
        supported_params=["condition_field", "operator", "threshold_value"]
    )
}


def get_available_tools_prompt_summary() -> str:
    """Returns a concise description of available abstract tools for the LLM."""
    lines = []
    for tool_id, meta in MOCK_TOOLS_REGISTRY.items():
        lines.append(f"- {tool_id} ({meta.name}, Type: {meta.type}): {meta.description}. Params: {', '.join(meta.supported_params)}")
    return "\n".join(lines)
