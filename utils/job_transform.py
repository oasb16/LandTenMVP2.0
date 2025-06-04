def build_job_from_incident(incident: dict) -> dict:
    """
    Convert incident record to a partial job dict for prefill or draft mode.

    Fields:
    - incident_id: from incident["incident_id"]
    - job_type: default "repair"
    - priority: from incident["priority"] or default "Medium"
    - description: from incident["issue"] or ""
    - price: default 0.0
    - created_by: static "landlord" (or override at use site)
    """
    return {
        "incident_id": incident.get("incident_id"),
        "job_type": "repair",
        "priority": incident.get("priority", "Medium"),
        "description": incident.get("issue", ""),
        "price": 0.0,
        "created_by": "landlord"
    }