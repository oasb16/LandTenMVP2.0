import os
import json
import uuid
from datetime import datetime
from utils.schema import incident_schema, IncidentSchema

LOG_FILE = "logs/incidents.json"

def create_incident(data: dict) -> dict:
    # Validate required fields
    required_fields = ["tenant_id", "property_id", "issue", "priority", "chat_data"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Validate types and enforce safe defaults
    if not isinstance(data["priority"], str) or not data["priority"].strip():
        raise ValueError("Priority must be a non-empty string.")

    if not isinstance(data["chat_data"], list):
        raise ValueError("Chat data must be a list.")

    # Handle created_by field
    created_by = data.get("created_by", "unknown")
    if not isinstance(created_by, str) or not created_by.strip():
        created_by = "unknown"

    # Generate incident_id and timestamp
    incident = IncidentSchema(
        incident_id=str(uuid.uuid4()),
        tenant_id=data["tenant_id"],
        property_id=data["property_id"],
        issue=data["issue"],
        priority=data["priority"],
        chat_data=data["chat_data"],
        timestamp=datetime.utcnow().isoformat(),
        created_by=created_by
    )

    # Ensure log file exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)

    # Append incident to log file
    with open(LOG_FILE, "r+") as f:
        incidents = json.load(f)
        incidents.append(incident)
        f.seek(0)
        json.dump(incidents, f, indent=4)

    return incident

def get_all_incidents() -> list:
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r") as f:
        return json.load(f)

def get_incident_by_id(incident_id: str) -> dict:
    incidents = get_all_incidents()
    for incident in incidents:
        if incident["incident_id"] == incident_id:
            return incident
    return None