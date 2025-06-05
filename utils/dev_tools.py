import streamlit as st
import os
import json
import logging
import uuid
from datetime import datetime
from botocore.exceptions import ClientError
import boto3

# Schema + utils
from utils.schema import IncidentSchema, JobSchema
from utils.db import _load_json

# Paths
INCIDENTS_LOG = "logs/incidents.json"
JOBS_LOG = "logs/jobs.json"

# S3
s3_client = boto3.client("s3",
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
    region_name=st.secrets["AWS_REGION"]
)

def _ensure_log(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f)
        st.info(f"📂 Created empty log: {path}")
    else:
        st.info(f"📄 Log exists: {path}")

# ---------------------------
# Seeder: Incidents + Jobs
# ---------------------------
def seed_incidents(n=3):
    _ensure_log(INCIDENTS_LOG)
    incidents = []
    for i in range(n):
        incidents.append(IncidentSchema(
            incident_id=str(uuid.uuid4()),
            tenant_id=f"tenant_{i+1}@example.com",
            property_id=f"property_{i+1}",
            issue=f"Test Issue #{i+1}",
            priority="High" if i % 2 == 0 else "Medium",
            chat_data=[
                {"sender": "tenant", "timestamp": datetime.utcnow().isoformat(), "message": f"Initial complaint #{i+1}"},
                {"sender": "agent", "timestamp": datetime.utcnow().isoformat(), "message": f"Agent acknowledged issue #{i+1}"}
            ],
            created_by=f"tenant_{i+1}@example.com"
        ))

    with open(INCIDENTS_LOG, "r+") as f:
        existing = json.load(f)
        existing.extend(incidents)
        f.seek(0)
        json.dump(existing, f, indent=2)
        f.truncate()

    st.session_state["incidents"] = _load_json(INCIDENTS_LOG)
    st.success(f"Seeded {len(incidents)} incidents.")

def seed_jobs_from_incidents():
    _ensure_log(JOBS_LOG)
    _ensure_log(INCIDENTS_LOG)

    incidents = _load_json(INCIDENTS_LOG)
    if not incidents:
        raise ValueError("No incidents found. Seed incidents first.")

    jobs = []
    for inc in incidents:
        jobs.append(JobSchema(
            job_id=str(uuid.uuid4()),
            incident_id=inc["incident_id"],
            job_type="plumbing" if "1" in inc["incident_id"] else "electrical",
            price=100.0,
            priority=inc.get("priority", "Medium"),
            description=inc["issue"],
            status="pending",
            assigned_contractor_id=None,
            accepted=None,
            timestamp=datetime.utcnow().isoformat(),
            created_by="landlord@example.com"
        ))

    with open(JOBS_LOG, "r+") as f:
        existing = json.load(f)
        existing.extend(jobs)
        f.seek(0)
        json.dump(existing, f, indent=2)
        f.truncate()

    st.session_state["jobs"] = _load_json(JOBS_LOG)
    st.success(f"Seeded {len(jobs)} jobs from incidents.")

# ---------------------------
# S3 Upload + Delete
# ---------------------------
def upload_incident_to_s3(incident_id, data):
    try:
        file_key = f"incidents/{incident_id}.json"
        s3_client.put_object(
            Bucket=st.secrets["S3_BUCKET"],
            Key=file_key,
            Body=json.dumps(data, indent=2),
            ContentType="application/json"
        )
        presigned_url = s3_client.generate_presigned_url("get_object",
            Params={"Bucket": st.secrets["S3_BUCKET"], "Key": file_key},
            ExpiresIn=300)
        st.success(f"✅ Incident uploaded: [view]({presigned_url})", icon="🪣")
        return presigned_url
    except ClientError as e:
        st.error(f"🚫 S3 Incident Upload Error: {e.response['Error']['Message']}")

def upload_job_to_s3(job_id, data):
    try:
        file_key = f"jobs/{job_id}.json"
        s3_client.put_object(
            Bucket=st.secrets["S3_BUCKET"],
            Key=file_key,
            Body=json.dumps(data, indent=2),
            ContentType="application/json"
        )
        presigned_url = s3_client.generate_presigned_url("get_object",
            Params={"Bucket": st.secrets["S3_BUCKET"], "Key": file_key},
            ExpiresIn=300)
        st.success(f"✅ Job uploaded: [view]({presigned_url})", icon="🛠️")
        return presigned_url
    except ClientError as e:
        st.error(f"🚫 S3 Job Upload Error: {e.response['Error']['Message']}")


def list_json_objects(prefix: str):
    """List all JSON file keys under a prefix like 'jobs/' or 'incidents/'."""
    try:
        response = s3_client.list_objects_v2(Bucket=st.secrets["S3_BUCKET"], Prefix=prefix)
        return [obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".json")]
    except ClientError as e:
        st.error(f"S3 List Error: {e.response['Error']['Message']}")
        return []

def load_json_from_s3(key: str):
    try:
        obj = s3_client.get_object(Bucket=st.secrets["S3_BUCKET"], Key=key)
        return json.loads(obj["Body"].read().decode("utf-8"))
    except ClientError as e:
        st.error(f"Failed to load {key}: {e.response['Error']['Message']}")
        return {}

def delete_all_from_s3(prefix: str):
    try:
        response = s3_client.list_objects_v2(Bucket=st.secrets["S3_BUCKET"], Prefix=prefix)
        if "Contents" not in response:
            st.warning(f"No files under `{prefix}`")
            return
        for obj in response["Contents"]:
            s3_client.delete_object(Bucket=st.secrets["S3_BUCKET"], Key=obj["Key"])
        st.success(f"🗑️ Deleted {len(response['Contents'])} `{prefix}` files from S3.")
    except ClientError as e:
        st.error(f"S3 Deletion Error: {e.response['Error']['Message']}")

def delete_all_incidents_from_s3():
    delete_all_from_s3("incidents/")

def delete_all_jobs_from_s3():
    delete_all_from_s3("jobs/")

# ---------------------------
# Main UI Expander
# ---------------------------
def dev_seed_expander():
    with st.expander("🧪 Test Data Tools", expanded=False):
        if st.button("🆕 Create Dummy Incidents + Jobs"):
            try:
                seed_incidents(n=3)
                seed_jobs_from_incidents()
                st.success("Dummy incidents and jobs created.")
            except Exception as e:
                st.error(f"❌ Failed to generate test data: {e}")

        if st.button("🗑️ Delete All Dummy Incidents + Jobs"):
            for file in [INCIDENTS_LOG, JOBS_LOG]:
                if os.path.exists(file):
                    os.remove(file)
                    st.success(f"Deleted {file}")
            st.session_state["incidents"] = []
            st.session_state["jobs"] = []

        # Re-check from disk
        st.session_state["incidents"] = _load_json(INCIDENTS_LOG)
        st.session_state["jobs"] = _load_json(JOBS_LOG)

        st.success(f"Incidents in session: {len(st.session_state.get('incidents', []))}")
        st.success(f"Jobs in session: {len(st.session_state.get('jobs', []))}")

        st.markdown("## ☁️ S3 Sync for Test Data")

        if st.button("☁️ Upload All Seeded Incidents to S3"):
            incidents = _load_json(INCIDENTS_LOG)
            st.session_state["incidents"] = incidents
            if not incidents:
                st.error("No incidents to upload. Please seed incidents first.")
            else:
                st.success(f"Uploading {len(incidents)} incidents to S3...")
                for inc in incidents:
                    upload_incident_to_s3(inc["incident_id"], inc)

        if st.button("☁️ Upload All Seeded Jobs to S3"):
            jobs = _load_json(JOBS_LOG)
            st.session_state["jobs"] = jobs
            if not jobs:
                st.error("No jobs to upload.")
            else:
                st.success(f"Uploading {len(jobs)} jobs to S3...")
                for job in jobs:
                    upload_job_to_s3(job["job_id"], job)

        if st.button("❌ Delete All Incidents from S3"):
            delete_all_incidents_from_s3()

        if st.button("❌ Delete All Jobs from S3"):
            delete_all_jobs_from_s3()
