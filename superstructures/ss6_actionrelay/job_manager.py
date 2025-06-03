import os
import json
import uuid
from datetime import datetime
from utils.schema import JobSchema
from ss5_summonengine.agent_handler import generate_action_message
from utils.db import append_chat_message, load_json, save_json
from utils.logger import log_info
from auto_assigner import suggest_best_contractor

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

    # Generate GPT action message
    agent_response = generate_action_message(data)

    # Format as chat message block
    chat_message = {
        "sender": "agent",
        "timestamp": datetime.utcnow().isoformat(),
        "message": agent_response["message"],
        "actions": agent_response.get("actions", [])
    }

    # Append to chat log
    thread_file = f"logs/chat_thread_{data['incident_id']}.json"

    if os.path.exists(thread_file):
        with open(thread_file, "r") as f:
            thread = json.load(f)
    else:
        thread = []

    thread.append(chat_message)

    with open(thread_file, "w") as f:
        json.dump(thread, f, indent=2)

    # After job is written to JSON log
    context = {
        "job_id": job.job_id,
        "incident_id": job.incident_id,
        "status": "created",
        "actor": st.session_state.get("user_id", "unknown")
    }

    try:
        agent_msg = generate_action_message(context)
        append_chat_message(context["incident_id"], agent_msg)
        log_info(f"[Agent Injected] Job Created → {agent_msg['message']}")
    except Exception as e:
        log_info(f"GPT Injection skipped: {e}")

    return job

def assign_job(job_id: str, contractor_email: str = None) -> dict:
    # Load jobs
    if not os.path.exists(LOG_FILE):
        raise ValueError("No jobs found.")

    with open(LOG_FILE, "r+") as f:
        jobs = json.load(f)
        job = next((j for j in jobs if j["job_id"] == job_id), None)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found.")

        if not contractor_email:
            # This list can later be dynamic based on status
            all_contractors = ["alex@fixitco.com", "sam@hvacpro.com"]
            contractor_email = suggest_best_contractor(job, all_contractors)

        if not contractor_email:
            raise ValueError("No contractor could be auto-assigned.")

        job["assigned_contractor_id"] = contractor_email
        f.seek(0)
        json.dump(jobs, f, indent=4)

        # After contractor_id written
        context = {
            "job_id": job_id,
            "incident_id": job["incident_id"],
            "status": "assigned",
            "actor": contractor_email
        }

        try:
            agent_msg = generate_action_message(context)
            append_chat_message(context["incident_id"], agent_msg)
            log_info(f"[Agent Injected] Job Assigned → {agent_msg['message']}")
        except Exception as e:
            log_info(f"GPT Injection skipped: {e}")

        return job

def accept_job(job_id: str, contractor_id: str) -> dict:
    # Load jobs
    if not os.path.exists(LOG_FILE):
        raise ValueError("No jobs found.")

    with open(LOG_FILE, "r+") as f:
        jobs = json.load(f)
        for job in jobs:
            if job["job_id"] == job_id:
                if job["accepted"] is not None:
                    raise ValueError("Decision already made")
                if job["assigned_contractor_id"] != contractor_id:
                    raise ValueError("Contractor ID does not match the assigned contractor.")
                job["accepted"] = True
                job["status"] = "accepted"
                job["timestamp"] = datetime.utcnow().isoformat()
                f.seek(0)
                json.dump(jobs, f, indent=4)

                # After status update to "accepted"
                context = {
                    "job_id": job_id,
                    "incident_id": job["incident_id"],
                    "status": "accepted",
                    "actor": contractor_id
                }

                try:
                    agent_msg = generate_action_message(context)
                    append_chat_message(context["incident_id"], agent_msg)
                    log_info(f"[Agent Injected] Job Accepted → {agent_msg['message']}")
                except Exception as e:
                    log_info(f"GPT Injection skipped: {e}")

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
                if job["accepted"] is not None:
                    raise ValueError("Decision already made")
                if job["assigned_contractor_id"] != contractor_id:
                    raise ValueError("Contractor ID does not match the assigned contractor.")
                job["accepted"] = False
                job["status"] = "rejected"
                job["timestamp"] = datetime.utcnow().isoformat()
                f.seek(0)
                json.dump(jobs, f, indent=4)
                return job

    raise ValueError(f"Job with ID {job_id} not found.")

def get_jobs_for_contractor(contractor_id: str) -> list:
    # Load jobs
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r") as f:
        jobs = json.load(f)
        return [
            job for job in jobs
            if job.get("assigned_contractor_id") == contractor_id and job.get("status") in ["pending", "assigned", "accepted"]
        ]

def propose_schedule(job_id: str, contractor_id: str, schedule: str) -> dict:
    # Load jobs
    if not os.path.exists(LOG_FILE):
        raise ValueError("No jobs found.")

    with open(LOG_FILE, "r+") as f:
        jobs = json.load(f)
        for job in jobs:
            if job["job_id"] == job_id:
                if job["assigned_contractor_id"] != contractor_id:
                    raise ValueError("Contractor ID does not match the assigned contractor.")
                job["proposed_schedule"] = schedule
                job["timestamp"] = datetime.utcnow().isoformat()
                f.seek(0)
                json.dump(jobs, f, indent=4)
                return job

    raise ValueError(f"Job with ID {job_id} not found.")

def complete_job(job_id: str, feedback: dict) -> bool:
    jobs = load_json("logs/jobs.json")
    job = next((j for j in jobs if j["job_id"] == job_id), None)
    if not job:
        raise ValueError("Job not found.")
    job["status"] = "completed"
    job["completed_at"] = datetime.now().isoformat()
    job["feedback"] = feedback
    save_json("logs/jobs.json", jobs)
    return True