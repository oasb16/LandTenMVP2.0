import json
import os
from typing import List, Dict
from utils.validation import validate_incident, validate_job
from datetime import datetime
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

def get_all_incidents() -> List[dict]:
    """Retrieve all incidents from the incidents log."""
    return _load_json(INCIDENTS_LOG)

def get_all_jobs() -> List[dict]:
    """Retrieve all jobs from the jobs log."""
    return _load_json(JOBS_LOG)

def patch_job(job_id: str, updates: dict) -> None:
    """Update specific fields of a job in the jobs log."""
    jobs = _load_json(JOBS_LOG)
    for job in jobs:
        if job.get("job_id") == job_id:
            job.update(updates)
            break
    else:
        raise ValueError(f"Job with ID {job_id} not found.")
    _write_json(JOBS_LOG, jobs)

def get_chat_thread(incident_id: str) -> List[dict]:
    path = f"logs/chat_thread_{incident_id}.json"
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_feedback(entry: dict):
    path = "logs/feedback.json"
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([entry], f, indent=2)
    else:
        with open(path, "r+") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)

def get_feedback_by_job(job_id: str) -> list:
    path = "logs/feedback.json"
    if not os.path.exists(path):
        return []
    with open(path) as f:
        feedback = json.load(f)
    return [f for f in feedback if f["job_id"] == job_id]

FEEDBACK_LOG = "logs/feedback.json"

def load_all_feedback() -> list:
    """Load all feedback entries from logs/feedback.json"""
    if not os.path.exists(FEEDBACK_LOG):
        return []
    try:
        with open(FEEDBACK_LOG, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def get_incident(incident_id: str) -> dict:
    """Retrieve a single incident by ID."""
    incidents = _load_json(INCIDENTS_LOG)
    for inc in incidents:
        if inc.get("incident_id") == incident_id:
            return inc
    raise ValueError(f"Incident with ID {incident_id} not found.")

def get_job_by_incident(incident_id: str) -> dict:
    """Retrieve the job linked to a given incident ID."""
    jobs = _load_json(JOBS_LOG)
    for job in jobs:
        if job.get("incident_id") == incident_id:
            return job
    return {}  # Return empty dict if not found
