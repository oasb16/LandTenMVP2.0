import os
import json
from datetime import datetime
from uuid import uuid4

INCIDENT_LOG_PATH = "logs/incidents.json"

def save_incident_from_media(transcript_or_caption, media_type="image", source="auto-agent"):
    os.makedirs("logs", exist_ok=True)

    incident = {
        "id": f"incident_{uuid4()}",
        "timestamp": datetime.utcnow().isoformat(),
        "summary": transcript_or_caption,
        "keywords": [],
        "source": source,
        "media_type": media_type,
        "status": "open"
    }

    if os.path.exists(INCIDENT_LOG_PATH):
        with open(INCIDENT_LOG_PATH, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.append(incident)

    with open(INCIDENT_LOG_PATH, "w") as f:
        json.dump(data, f, indent=2)
