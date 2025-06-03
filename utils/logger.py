import json
import os
from datetime import datetime

LOG_PATH = "logs/agent_analytics.json"

def log_agent_event(event: dict):
    event["timestamp"] = datetime.utcnow().isoformat()
    try:
        if not os.path.exists(LOG_PATH):
            with open(LOG_PATH, "w") as f:
                json.dump([event], f, indent=2)
        else:
            with open(LOG_PATH, "r+") as f:
                data = json.load(f)
                data.append(event)
                f.seek(0)
                json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Logger] Failed to log agent event: {e}")