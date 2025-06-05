import streamlit as st
import os
import json
import logging
import uuid
from datetime import datetime
from botocore.exceptions import ClientError
import boto3
from utils.db import _load_json

# --- Constants ---
INCIDENTS_LOG = "logs/incidents.json"
JOBS_LOG = "logs/jobs.json"

# --- S3 Client ---
s3_client = boto3.client("s3",
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
    region_name=st.secrets["AWS_REGION"]
)

# --- Log Helpers ---
def _ensure_log(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f)
            st.success(f"Created log file: {path}", icon="📂")
    else:
        st.info(f"Log file already exists: {path}", icon="📄")
            

# --- Schema Imports ---
from utils.schema import IncidentSchema, JobSchema


# --- Seeder Functions ---
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
        # st.session_state["incidents"] = existing
        f.seek(0)
        json.dump(existing, f, indent=2)
        f.truncate()  # <-- ensure no residual JSON remains

        # Now load cleanly from disk into session (ensures sync)
        with open(INCIDENTS_LOG, "r") as refreshed:
            synced = json.load(refreshed)
            st.session_state["incidents"] = synced
        st.success(f"Seeded {len(incidents)} incidents.")


def seed_jobs_from_incidents():
    """Generate dummy jobs for each incident."""
    _ensure_log(JOBS_LOG)
    _ensure_log(INCIDENTS_LOG)

    with open(INCIDENTS_LOG, "r") as f:
        incidents = json.load(f)
        st.session_state["incidents"] = incidents

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
        st.session_state["jobs"] = existing
        st.success(f"Seeded {len(jobs)} jobs from incidents.")
        f.seek(0)
        json.dump(existing, f, indent=2)


# --- S3 Uploaders ---
def upload_incident_to_s3(incident_id, data):
    try:
        file_key = f"incidents/{incident_id}.json"

        s3_client.put_object(
            Bucket=st.secrets["S3_BUCKET"],
            Key=file_key,
            Body=json.dumps(data, indent=2),
            ContentType="application/json"
        )

        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": st.secrets["S3_BUCKET"], "Key": file_key},
            ExpiresIn=300
        )

        st.success(f"✅ Incident uploaded: [view]({presigned_url})", icon="🪣")
        return presigned_url

    except ClientError as e:
        logging.error(f"S3 Upload Error: {e.response['Error']['Message']}")
        st.error(f"S3 Upload Error: {e.response['Error']['Message']}")
        return None


def upload_job_to_s3(job_id, data):
    try:
        file_key = f"jobs/{job_id}.json"

        s3_client.put_object(
            Bucket=st.secrets["S3_BUCKET"],
            Key=file_key,
            Body=json.dumps(data, indent=2),
            ContentType="application/json"
        )

        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": st.secrets["S3_BUCKET"], "Key": file_key},
            ExpiresIn=300
        )

        st.success(f"✅ Job uploaded: [view]({presigned_url})", icon="🛠️")
        return presigned_url

    except ClientError as e:
        logging.error(f"S3 Upload Error: {e.response['Error']['Message']}")
        st.error(f"S3 Upload Error: {e.response['Error']['Message']}")
        return None


# --- S3 Deletion Helpers ---
def delete_all_from_s3(prefix: str):
    bucket = st.secrets["S3_BUCKET"]
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if "Contents" not in response:
            st.warning(f"No S3 files found under prefix `{prefix}`.")
            return

        for obj in response["Contents"]:
            s3_client.delete_object(Bucket=bucket, Key=obj["Key"])
            logging.info(f"Deleted {obj['Key']} from S3")

        st.success(f"✅ All `{prefix}` entries deleted from S3. {len(response['Contents'])} files removed.", icon="🗑️")

    except ClientError as e:
        logging.error(f"S3 Delete Error: {e}")
        st.error(f"Failed to delete from S3: {e.response['Error']['Message']}")


def delete_all_incidents_from_s3():
    delete_all_from_s3("incidents/")


def delete_all_jobs_from_s3():
    delete_all_from_s3("jobs/")


# --- Unified Expander UI ---
def dev_seed_expander():
    with st.expander("🧪 Test Data Tools", expanded=False):
        if "incidents" not in st.session_state:
            st.session_state["incidents"] = _load_json("logs/incidents.json")

        if st.button("🆕 Create Dummy Incidents + Jobs"):
            try:
                seed_incidents(n=3)
                seed_jobs_from_incidents()
                st.session_state["incidents"] = _load_json(INCIDENTS_LOG)
                st.session_state["jobs"] = _load_json(JOBS_LOG)
                st.success("Dummy incidents and jobs created.")
            except Exception as e:
                st.error(f"Error generating test data: {e}")

        if st.button("🗑️ Delete All Dummy Incidents + Jobs"):
            try:
                for file in [INCIDENTS_LOG, JOBS_LOG]:
                    if os.path.exists(file):
                        os.remove(file)
                        st.success(f"Deleted {file}")
                st.session_state["incidents"] = []
                st.session_state["jobs"] = []
            except Exception as e:
                st.error(f"Error deleting test data: {e}")

        st.success(f"Incidents in session: {len(st.session_state.get('incidents', []))}")
        st.success(f"Jobs in session: {len(st.session_state.get('jobs', []))}")

        st.markdown("## ☁️ S3 Sync for Test Data")

        if st.button("☁️ Upload All Seeded Incidents to S3"):
            if "incidents" not in st.session_state:
                st.error("No incidents found in session state. Please seed incidents first.")
                return
            for inc in st.session_state.get("incidents", []):
                upload_incident_to_s3(inc["incident_id"], inc)

        if st.button("☁️ Upload All Seeded Jobs to S3"):
            for job in st.session_state.get("jobs", []):
                upload_job_to_s3(job["job_id"], job)

        if st.button("❌ Delete All Incidents from S3"):
            delete_all_incidents_from_s3()

        if st.button("❌ Delete All Jobs from S3"):
            delete_all_jobs_from_s3()
