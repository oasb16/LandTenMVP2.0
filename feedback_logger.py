from utils.db import load_json, save_json
from datetime import datetime

def log_feedback(job_id: str, rating: int, comment: str, actor: str) -> dict:
    entry = {
        "job_id": job_id,
        "rating": rating,
        "comment": comment,
        "submitted_by": actor,
        "timestamp": datetime.now().isoformat()
    }
    feedback_log = load_json("logs/feedback.json")
    feedback_log.append(entry)
    save_json("logs/feedback.json", feedback_log)
    return entry