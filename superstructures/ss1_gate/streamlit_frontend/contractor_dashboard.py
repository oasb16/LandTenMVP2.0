# contractor_dashboard.py

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
    delete_all_threads_from_dynamodb,
    upload_thread_to_s3,
    save_message_to_dynamodb
)
from superstructures.ss6_actionrelay.job_manager import (
    get_jobs_for_contractor, accept_job, reject_job, propose_schedule
)

# -- Config
CLIENT_ID = st.secrets.get("COGNITO_CLIENT_ID")
COGNITO_DOMAIN = "https://us-east-1liycxnadt.auth.us-east-1.amazoncognito.com"
REDIRECT_URI = "https://landtenmvp20.streamlit.app/"
WEBSOCKET_SERVER_URL = "ws://localhost:8765"

def render_contractor_dashboard():
    st.header("Contractor Dashboard")

    contractor_id = st.session_state.get("user_id", "")
    if not contractor_id:
        st.error("User ID missing from session.")
        return

    assigned_jobs = get_jobs_for_contractor(contractor_id)

    for job in assigned_jobs:
        with st.expander(f"Job: {job['description']}"):
            st.write(f"**Priority**: {job['priority']}")
            st.write(f"**Status**: {job['status']}")
            st.write(f"**Proposed Schedule**: {job.get('proposed_schedule', 'Not proposed')}")

            if job["status"] == "pending":
                with st.form(key=f"decision_form_{job['job_id']}"):
                    decision = st.radio("Decision", ["Accept", "Reject"], horizontal=True)
                    submitted = st.form_submit_button("Submit Decision")
                    if submitted:
                        try:
                            if decision == "Accept":
                                accept_job(job["job_id"], contractor_id)
                                st.success("Job accepted.")
                            else:
                                reject_job(job["job_id"], contractor_id)
                                st.warning("Job rejected.")
                        except ValueError as e:
                            st.error(str(e))

            elif job["status"] == "accepted":
                with st.form(key=f"schedule_form_{job['job_id']}"):
                    date = st.date_input("Propose Date")
                    time = st.time_input("Propose Time")
                    submitted = st.form_submit_button("Propose Schedule")
                    if submitted:
                        schedule_str = f"{date} {time}"
                        try:
                            propose_schedule(job["job_id"], contractor_id, schedule_str)
                            st.success("Schedule proposed.")
                        except ValueError as e:
                            st.error(str(e))

def run_contractor_dashboard():
    html("<style>body { font-family: 'SF Pro Display', sans-serif; }</style>")

    @st.cache_resource
    def start_websocket_server():
        subprocess.Popen(["python", "websocket_server.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def start_websocket_client():
        async def listen():
            async with websockets.connect(WEBSOCKET_SERVER_URL) as websocket:
                while True:
                    message = await websocket.recv()
                    notification = json.loads(message)
                    if notification.get("type") == "notification":
                        st.toast(notification.get("message"))
        threading.Thread(target=lambda: asyncio.run(listen()), daemon=True).start()

    def generate_dummy_threads():
        dummy_threads = []
        for i in range(5):
            thread_id = str(uuid4())
            dummy_data = {
                "thread_id": thread_id,
                "chat_log": [
                    {
                        "id": str(uuid4()), "timestamp": datetime.utcnow().isoformat(),
                        "role": "contractor", "message": f"Dummy message {i+1} from contractor", "thread_id": thread_id, "email": "dummy@example.com"
                    },
                    {
                        "id": str(uuid4()), "timestamp": datetime.utcnow().isoformat(),
                        "role": "agent", "message": f"Agent response {i+1}", "thread_id": thread_id, "email": "dummy@example.com"
                    }
                ]
            }
            try:
                for msg in dummy_data["chat_log"]:
                    save_message_to_dynamodb(thread_id, msg)
                upload_thread_to_s3(thread_id, dummy_data["chat_log"])
                dummy_threads.append(thread_id)
            except Exception as e:
                logging.error(f"[Thread Error] {thread_id}: {e}")
                st.error(f"Error with thread {thread_id}: {e}")
        return dummy_threads

    def fetch_and_display_threads():
        threads = get_all_threads_from_dynamodb()
        unique = {t['thread_id']: t for t in threads if 'thread_id' in t}
        sorted_threads = sorted(unique.values(), key=lambda x: x.get('timestamp', ''), reverse=True)
        return ["Select a Thread"] + [t['thread_id'] for t in sorted_threads]

    # -- Sidebar
    with st.sidebar:
        st.title(f"🔧 **{st.session_state.get('email', 'Unknown')}**")
        if st.button("Logout"):
            try:
                st.session_state.clear()
                logout_url = f"{COGNITO_DOMAIN}/logout?client_id={CLIENT_ID}&logout_uri={REDIRECT_URI}"
                st.markdown(f"[🔓 Logged out — click to re-login]({logout_url})")
                st.stop()
            except Exception as e:
                st.error(f"Logout error: {str(e)}")

        thread_options = fetch_and_display_threads()
        selected = st.selectbox("💬 Select a Thread", options=thread_options)

        if selected != "Select a Thread":
            if st.session_state.get('selected_thread') != selected:
                st.session_state['selected_thread'] = selected
                chat_log = sorted(
                    [t for t in get_all_threads_from_dynamodb() if t['thread_id'] == selected],
                    key=lambda x: x['timestamp']
                )
                st.session_state['chat_log'] = list({t['id']: t for t in chat_log}.values())

        with st.expander("🛠️ Thread Tools", expanded=False):
            if st.button("🧹 Delete All Threads"):
                delete_all_threads_from_dynamodb()
                st.session_state['selected_thread'] = None
                st.success("Threads cleared.")
                st.rerun()

            if st.button("❎ Delete Empty Threads"):
                prune_empty_threads()

            if st.button("🎯 Generate Dummy Threads"):
                threads = generate_dummy_threads()
                st.success(f"Dummy threads: {', '.join(threads)}")
                st.rerun()

    # -- Layout: Title + Chat
    persona = st.session_state.get("persona", "contractor").capitalize()
    st.title(f"🏗️ {persona} Dashboard")

    if st.session_state.get("selected_thread"):
        with st.expander("📜 Messages", expanded=False):
            st.subheader(f"📂 Thread: {st.session_state['selected_thread']}")
            for msg in st.session_state.get('chat_log', []):
                role = msg.get('role', 'Unknown').capitalize()
                content = msg.get('message', '[No message]')
                if role == 'Agent' and 'Agent error' in content:
                    content = '[Agent encountered an error.]'
                st.markdown(f"**{role}**: {content}")

    # -- Chat Core
    run_chat_core()

    # -- Role-Specific Panel
    st.subheader("📇 Details")
    st.markdown("### 🔧 Jobs and Schedule")
    render_contractor_dashboard()

    # -- Responsive Styling
    html("""
    <style>
    @media (max-width: 768px) {
        .css-1lcbmhc { flex-direction: column !important; }
    }
    </style>
    """)

    # -- WebSocket Activation
    start_websocket_server()
    start_websocket_client()
