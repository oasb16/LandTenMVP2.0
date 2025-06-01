import json
import os
from typing import List, Dict
from utils.validation import validate_incident, validate_job

INCIDENTS_LOG = "logs/incidents.json"
JOBS_LOG = "logs/jobs.json"

def _load_json(filepath: str) -> List[Dict]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def _write_json(filepath: str, data: List[Dict]):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def save_incident(incident_dict: dict) -> None:
    validate_incident(incident_dict)
    records = _load_json(INCIDENTS_LOG)
    records.append(incident_dict)
    _write_json(INCIDENTS_LOG, records)

def get_incidents_by_user(user_id: str) -> List[dict]:
    records = _load_json(INCIDENTS_LOG)
    return [i for i in records if i.get("tenant_id") == user_id]

def save_job(job_dict: dict) -> None:
    validate_job(job_dict)
    records = _load_json(JOBS_LOG)
    records.append(job_dict)
    _write_json(JOBS_LOG, records)

def get_jobs_by_contractor(user_id: str) -> List[dict]:
    records = _load_json(JOBS_LOG)
    return [j for j in records if j.get("assigned_contractor_id") == user_id]

def convert_incident_to_job(incident_id: str, job_fields: dict) -> dict:
    incidents = _load_json(INCIDENTS_LOG)
    matching = next((i for i in incidents if i["incident_id"] == incident_id), None)
    if not matching:
        raise ValueError(f"Incident {incident_id} not found")
    new_job = {
        "incident_id": incident_id,
        "job_type": job_fields.get("job_type", "repair"),
        "priority": matching.get("priority", "Medium"),
        "description": job_fields.get("description", matching.get("issue", "")),
        "price": job_fields.get("price", 0.0),
        "created_by": job_fields.get("created_by", "landlord"),
        "status": "pending",
        "job_id": f"job_{incident_id}",  # or use uuid
    }
    save_job(new_job)
    return new_job