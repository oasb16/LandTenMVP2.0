import json
import os
from datetime import datetime

FEEDBACK_PATH = "logs/feedback.json"

def submit_feedback(feedback: dict):
    required = {"job_id", "submitted_by", "role", "rating", "notes"}
    if not required.issubset(feedback.keys()):
        raise ValueError("Missing required feedback fields")

    feedback["timestamp"] = datetime.utcnow().isoformat()

    # Prevent duplicate submission by same user-role-job combo
    if os.path.exists(FEEDBACK_PATH):
        with open(FEEDBACK_PATH, "r") as f:
            existing = json.load(f)
    else:
        existing = []

    if any(
        f["job_id"] == feedback["job_id"] and
        f["submitted_by"] == feedback["submitted_by"] and
        f["role"] == feedback["role"]
        for f in existing
    ):
        raise ValueError("Feedback already submitted for this job by this user")

    existing.append(feedback)

    with open(FEEDBACK_PATH, "w") as f:
        json.dump(existing, f, indent=2)