import json
from collections import defaultdict
import os

FEEDBACK_PATH = "logs/feedback.json"
JOB_PATH = "logs/jobs.json"

def compute_contractor_trust_scores() -> dict:
    """
    Computes average rating score per contractor based on feedback.json + jobs.json.
    Returns: Dict[contractor_id: str, avg_rating: float]
    """
    if not os.path.exists(FEEDBACK_PATH) or not os.path.exists(JOB_PATH):
        return {}

    with open(FEEDBACK_PATH, "r") as f:
        feedback = json.load(f)

    with open(JOB_PATH, "r") as f:
        jobs = json.load(f)

    # Map job_id to contractor_id
    job_to_contractor = {job["job_id"]: job.get("assigned_to") for job in jobs if "assigned_to" in job}

    contractor_ratings = defaultdict(list)

    for fb in feedback:
        contractor_id = job_to_contractor.get(fb["job_id"])
        if contractor_id and isinstance(fb.get("rating"), int):
            contractor_ratings[contractor_id].append(fb["rating"])

    # Compute average
    return {
        contractor_id: round(sum(ratings) / len(ratings), 2)
        for contractor_id, ratings in contractor_ratings.items()
        if ratings
    }