# landlord_dashboard.py

import streamlit as st
import asyncio
import websockets
import threading
import subprocess
import json
import logging
from datetime import datetime
from uuid import uuid4
from urllib.parse import quote
from streamlit.components.v1 import html

# -- Core Modules --
from superstructures.ss1_gate.streamlit_frontend.ss1_gate_app import run_login
from superstructures.ss2_pulse.ss2_pulse_app import run_router
from superstructures.ss3_trichatcore.tri_chat_core import run_chat_core, prune_empty_threads
from superstructures.ss5_summonengine.summon_engine import (
    get_all_threads_from_dynamodb,
    save_message_to_dynamodb
)

# Import the new shared service module
from superstructures.ss1_gate.shared.thread_job_service import (
    generate_dummy_threads,
    fetch_and_display_threads,
    delete_all_threads,
    prune_empty_threads
)

from superstructures.ss6_actionrelay.incident_manager import get_all_incidents
from superstructures.ss6_actionrelay.job_manager import (
    create_job, assign_job, get_all_jobs
)

from superstructures.ss5_summonengine.agent_handler import process_agent_tag

# -- Config
CLIENT_ID = st.secrets.get("COGNITO_CLIENT_ID")
COGNITO_DOMAIN = "https://us-east-1liycxnadt.auth.us-east-1.amazoncognito.com"
REDIRECT_URI = "https://landtenmvp20.streamlit.app/"
WEBSOCKET_SERVER_URL = "ws://localhost:8765"

def run_landlord_dashboard():
    st.header("Landlord Dashboard")
    user_id = st.session_state.get("user_id", "")

    st.subheader("📍 View Reported Incidents")
    incidents = get_all_incidents()

    for incident in incidents:
        with st.expander(f"Incident: {incident['issue']}"):
            st.write(f"**Priority**: {incident['priority']}")
            st.write(f"**Reported By**: {incident.get('created_by', 'Unknown')}")
            st.write("**Chat Log:**")
            for msg in incident.get("chat_data", []):
                st.markdown(f"- **{msg['sender']}** @ {msg['timestamp']}: {msg['message']}")

            # Analyze with Agent
            agent_key = f"agent_output_{incident['incident_id']}"
            if st.button("🧠 Analyze with Agent", key=agent_key):
                try:
                    suggestion = process_agent_tag(incident["chat_data"])
                    st.session_state[agent_key] = suggestion
                    st.success("Agent analysis complete. Prefilling job form.")
                except Exception as e:
                    st.warning("Agent failed to process chat.")
                    st.session_state[agent_key] = None
                    print(f"❌ Agent analysis failed: {e}")

            # Display GPT suggestion if available
            suggestion = st.session_state.get(agent_key)
            if suggestion:
                st.subheader("🔍 Agent Suggestion")
                st.markdown(f"**Job Type**: {suggestion['job_type']}")
                st.markdown(f"**Priority**: {suggestion['priority']}")
                st.markdown(f"**Estimated Price**: {suggestion['price']}")
                st.markdown(f"**Description**: {suggestion['description']}")

            # Job Creation Form (Prefilled if suggestion exists)
            with st.form(key=f"create_job_form_{incident['incident_id']}"):
                st.markdown("### Create Job from This Incident")
                job_type = st.text_input("Job Type", value=suggestion.get("job_type", "") if suggestion else "")
                description = st.text_area("Job Description", value=suggestion.get("description", "") if suggestion else "")
                price = st.number_input("Price", min_value=0.0, format="%.2f", value=suggestion.get("price", 0.0) if suggestion and suggestion.get("price") else 0.0)
                priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(suggestion.get("priority", "Medium")) if suggestion else 1)
                submit = st.form_submit_button("Create Job")
                if submit:
                    try:
                        create_job({
                            "incident_id": incident["incident_id"],
                            "job_type": job_type,
                            "description": description,
                            "price": price,
                            "priority": priority,
                            "created_by": user_id
                        })
                        st.success("Job created.")
                    except Exception as e:
                        st.error(f"Error creating job: {e}")

    st.subheader("🔧 Assign Contractors to Jobs")
    try:
        jobs = get_all_jobs()
    except:
        jobs = []

    for job in jobs:
        with st.expander(f"Job: {job['description']}"):
            st.write(f"**Status**: {job['status']}")
            st.write(f"**Priority**: {job['priority']}")
            st.write(f"**Accepted**: {job.get('accepted', '—')}")
            st.write(f"**Proposed Schedule**: {job.get('proposed_schedule', '—')}")

            if not job.get("assigned_contractor_id"):
                with st.form(key=f"assign_form_{job['job_id']}"):
                    contractor_id = st.text_input("Contractor ID")
                    submit = st.form_submit_button("Assign Contractor")
                    if submit:
                        try:
                            assign_job(job["job_id"], contractor_id)
                            st.success("Contractor assigned.")
                        except Exception as e:
                            st.error(f"Assignment failed: {e}")
            else:
                st.info(f"Assigned to contractor: {job['assigned_contractor_id']}")
