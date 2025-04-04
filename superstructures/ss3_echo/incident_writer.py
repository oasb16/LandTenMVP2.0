import os
import json

def save_incident(incident):
    os.makedirs("incidents", exist_ok=True)
    with open(f"incidents/{incident['id']}.json", "w") as f:
        json.dump(incident, f, indent=2)