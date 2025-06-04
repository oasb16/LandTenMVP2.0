# scripts/seed_test_data.py

import json
import os
import uuid
from datetime import datetime
from utils.schema import IncidentSchema, JobSchema

INCIDENTS_LOG = "logs/incidents.json"
JOBS_LOG = "logs/jobs.json"

def _ensure_log(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f)

def seed_incidents(n=3):
    """Create dummy incident entries."""
    _ensure_log(INCIDENTS_LOG)

    incidents = []
    for i in range(n):
        incident = IncidentSchema(
            incident_id=str(uuid.uuid4()),
            tenant_id=f"tenant_{i+1}@example.com",
            property_id=f"property_{i+1}",
            issue=f"Test Issue #{i+1}",
            priority="High" if i % 2 == 0 else "Medium",
            chat_data=[
                {
                    "sender": "tenant",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Initial complaint #{i+1}"
                },
                {
                    "sender": "agent",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Agent acknowledged issue #{i+1}"
                }
            ],
            created_by=f"tenant_{i+1}@example.com"
        )
        incidents.append(incident)

    with open(INCIDENTS_LOG, "r+") as f:
        existing = json.load(f)
        existing.extend(incidents)
        f.seek(0)
        json.dump(existing, f, indent=2)

def seed_jobs_from_incidents():
    """Generate dummy jobs for each incident."""
    _ensure_log(JOBS_LOG)
    _ensure_log(INCIDENTS_LOG)

    with open(INCIDENTS_LOG, "r") as f:
        incidents = json.load(f)

    if not incidents:
        raise ValueError("No incidents found. Seed incidents first.")

    jobs = []
    for incident in incidents:
        job = JobSchema(
            job_id=str(uuid.uuid4()),
            incident_id=incident["incident_id"],
            job_type="plumbing" if "1" in incident["incident_id"] else "electrical",
            price=100.0,
            priority=incident.get("priority", "Medium"),
            description=incident["issue"],
            status="pending",
            assigned_contractor_id=None,
            accepted=None,
            timestamp=datetime.utcnow().isoformat(),
            created_by="landlord@example.com"
        )
        jobs.append(job)

    with open(JOBS_LOG, "r+") as f:
        existing = json.load(f)
        existing.extend(jobs)
        f.seek(0)
        json.dump(existing, f, indent=2)
