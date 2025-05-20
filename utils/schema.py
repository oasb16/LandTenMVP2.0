from typing import TypedDict, List, Optional

# Define schema for chat messages
class ChatMessage(TypedDict):
    sender: str  # Who sent the message
    timestamp: str  # ISO format timestamp
    message: str  # Plain text message
    media: Optional[str]  # Path or URL to media, if present

class IncidentSchema(TypedDict):
    incident_id: str
    tenant_id: str
    property_id: str
    issue: str
    priority: str
    chat_data: List[ChatMessage]  # Updated to use ChatMessage schema
    timestamp: str
    created_by: Optional[str]  # Role/user who initiated the incident

class JobSchema(TypedDict):
    job_id: str
    incident_id: str
    job_type: str
    price: float
    priority: str
    description: str
    status: str
    assigned_contractor_id: Optional[str]
    accepted: Optional[bool]
    timestamp: str
    created_by: Optional[str]  # Role/user who created the job
    proposed_schedule: Optional[str]  # Schedule proposed by contractor (e.g., date/time string)

def build_incident_template() -> IncidentSchema:
    """Returns a default-structured incident with placeholders."""
    return IncidentSchema(
        incident_id="",
        tenant_id="",
        property_id="",
        issue="",
        priority="",
        chat_data=[],
        timestamp="",
        created_by=None
    )