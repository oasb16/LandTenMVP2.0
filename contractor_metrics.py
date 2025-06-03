import json
from statistics import mean

def build_scorecard(contractor_id: str,
                    jobs_path="logs/jobs.json",
                    feedback_path="logs/feedback.json") -> dict:
    try:
        with open(jobs_path) as jf:
            jobs = json.load(jf)
        with open(feedback_path) as ff:
            feedback = json.load(ff)

        completed_jobs = [j for j in jobs if j.get("assigned_contractor_id") == contractor_id]
        contractor_feedback = [f for f in feedback if f.get("contractor_id") == contractor_id]

        ratings = [f["rating"] for f in contractor_feedback if isinstance(f.get("rating"), (int, float))]
        comments = [f["comment"] for f in contractor_feedback if f.get("comment")]

        return {
            "contractor_id": contractor_id,
            "avg_rating": round(mean(ratings), 2) if ratings else None,
            "jobs_completed": len(completed_jobs),
            "last_feedback": comments[-3:]
        }

    except Exception as e:
        return {"contractor_id": contractor_id, "error": str(e)}