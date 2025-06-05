# utils/dev_tools.py

import streamlit as st
import os, logging
from scripts.seed_test_data import seed_incidents, seed_jobs_from_incidents
from utils.db import _load_json
from utils.s3_uploader import upload_job_to_s3, upload_incident_to_s3


def dev_seed_expander():
    with st.expander("🧪 Test Data Toolsssss", expanded=False):
        if st.button("🆕 Create Dummy Incidents + Jobs"):
            try:
                seed_incidents(n=3)
                seed_jobs_from_incidents()

                # Reload from disk AFTER seeding and BEFORE rerun
                st.session_state["incidents"] = _load_json("logs/incidents.json")
                st.session_state["jobs"] = _load_json("logs/jobs.json")
                st.success("Dummy incidents and jobs created.")
                # DO NOT st.rerun() here!
            except Exception as e:
                st.error(f"Error generating test data: {e}")

        if st.button("🗑️ Delete All Dummy Incidents + Jobs"):
            try:
                for file in ["logs/incidents.json", "logs/jobs.json"]:
                    if os.path.exists(file):
                        os.remove(file)
                        st.success(f"Deleted {file}")
                st.session_state["incidents"] = []
                st.session_state["jobs"] = []
            except Exception as e:
                st.error(f"Error deleting test data: {e}")
        
        st.success(f"Incidents in session: {len(st.session_state.get('incidents', []))}")
        st.success(f"Jobs in session: {len(st.session_state.get('jobs', []))}")

        st.markdown("## 🧪 S3 Sync for Test Data")

        if st.button("☁️ Upload All Seeded Incidents to S3"):
            for inc in st.session_state.get("incidents", []):
                upload_incident_to_s3(inc["incident_id"], inc)

        if st.button("☁️ Upload All Seeded Jobs to S3"):
            for job in st.session_state.get("jobs", []):
                upload_job_to_s3(job["job_id"], job)

