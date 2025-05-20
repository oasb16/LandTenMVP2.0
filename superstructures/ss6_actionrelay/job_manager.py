import os
import json
import uuid
from datetime import datetime
from utils.schema import JobSchema

LOG_FILE = "logs/jobs.json"

def create_job(data: dict) -> dict:
    # Validate required fields
    required_fields = ["incident_id", "job_type", "price", "priority", "description"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Handle created_by field
    created_by = data.get("created_by", "unknown")
    if not isinstance(created_by, str) or not created_by.strip():
        created_by = "unknown"

    # Generate job_id and timestamp
    job = JobSchema(
        job_id=str(uuid.uuid4()),
        incident_id=data["incident_id"],
        job_type=data["job_type"],
        price=data["price"],
        priority=data["priority"],
        description=data["description"],
        status="pending",
        assigned_contractor_id=None,
        accepted=None,
        timestamp=datetime.utcnow().isoformat(),
        created_by=created_by
    )

    # Ensure log file exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)

    # Append job to log file
    with open(LOG_FILE, "r+") as f:
        jobs = json.load(f)
        jobs.append(job)
        f.seek(0)
        json.dump(jobs, f, indent=4)

    return job

def assign_job(job_id: str, contractor_id: str) -> dict:
    # Load jobs
    if not os.path.exists(LOG_FILE):
        raise ValueError("No jobs found.")

    with open(LOG_FILE, "r+") as f:
        jobs = json.load(f)
        for job in jobs:
            if job["job_id"] == job_id:
                job["assigned_contractor_id"] = contractor_id
                f.seek(0)
                json.dump(jobs, f, indent=4)
                return job

    raise ValueError(f"Job with ID {job_id} not found.")

def accept_job(job_id: str, contractor_id: str) -> dict:
    # Load jobs
    if not os.path.exists(LOG_FILE):
        raise ValueError("No jobs found.")

    with open(LOG_FILE, "r+") as f:
        jobs = json.load(f)
        for job in jobs:
            if job["job_id"] == job_id:
                if job["assigned_contractor_id"] != contractor_id:
                    raise ValueError("Contractor ID does not match the assigned contractor.")
                job["accepted"] = True
                job["status"] = "accepted"
                f.seek(0)
                json.dump(jobs, f, indent=4)
                return job

    raise ValueError(f"Job with ID {job_id} not found.")

def reject_job(job_id: str, contractor_id: str) -> dict:
    # Load jobs
    if not os.path.exists(LOG_FILE):
        raise ValueError("No jobs found.")

    with open(LOG_FILE, "r+") as f:
        jobs = json.load(f)
        for job in jobs:
            if job["job_id"] == job_id:
                if job["assigned_contractor_id"] != contractor_id:
                    raise ValueError("Contractor ID does not match the assigned contractor.")
                job["accepted"] = False
                job["status"] = "rejected"
                f.seek(0)
                json.dump(jobs, f, indent=4)
                return job

    raise ValueError(f"Job with ID {job_id} not found.")