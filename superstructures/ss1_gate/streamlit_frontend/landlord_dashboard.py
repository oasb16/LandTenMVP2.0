# landlord_dashboard.py

import streamlit as st
import asyncio
import websockets
import threading
import subprocess
import json
import logging
import os
from datetime import datetime
from uuid import uuid4
from urllib.parse import quote
from streamlit.components.v1 import html
# List all Jobs Overview (Table View
from utils.dev_tools import list_json_objects, load_json_from_s3
import pandas as pd
import math
from superstructures.ss7_intelprint.report_engine import generate_pdf_report
# from ss5_summonengine.chat_summarizer import summarize_chat_thread
# from superstructures.ss6_actionrelay.job_manager import create_job

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

from utils.trust_score import compute_contractor_trust_scores
from utils.db import load_all_feedback
from superstructures.ss7_intelprint.report_engine import generate_pdf_report

# -- Config
CLIENT_ID = st.secrets.get("COGNITO_CLIENT_ID")
COGNITO_DOMAIN = "https://us-east-1liycxnadt.auth.us-east-1.amazoncognito.com"
REDIRECT_URI = "https://landtenmvp20.streamlit.app/"
WEBSOCKET_SERVER_URL = "ws://localhost:8765"

def load_incidents():
    log_path = "logs/incidents.json"
    if not os.path.exists(log_path):
        return []
    with open(log_path, "r") as f:
        return json.load(f)

def run_landlord_dashboard():
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

    # -- Sidebar
    with st.sidebar:
        st.title(f"🏠 **{st.session_state.get('email', 'Unknown')}**")
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
                delete_all_threads()
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
    persona = st.session_state.get("persona", "landlord").capitalize()
    st.title(f"🧱 {persona} Dashboard")

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

    import pandas as pd
    # Fetch jobs + incidents from S3
    job_keys = list_json_objects("jobs/")
    incident_keys = list_json_objects("incidents/")

    jobs = [load_json_from_s3(k) for k in job_keys]
    incidents = [load_json_from_s3(k) for k in incident_keys]

    st.subheader("📇 Details")
    with st.expander("🏗️ Jobs Overview (Paginated)", expanded=True):
        try:


            # Merge jobs with incidents
            merged = []
            for job in jobs:
                match = next((inc for inc in incidents if inc.get("incident_id") == job.get("incident_id")), {})
                merged.append({
                    "Job ID": job.get("job_id"),
                    "Incident": match.get("issue", "N/A"),
                    "Priority": job.get("priority", "N/A"),
                    "Type": job.get("job_type", "N/A"),
                    "Price": job.get("price"),
                    "Assigned To": job.get("assigned_contractor_id", "—"),
                    "Accepted": "Yes" if job.get("accepted") else "No",
                    "Status": job.get("status"),
                    "Created By": job.get("created_by", "N/A"),
                    "Timestamp": job.get("timestamp", "—")
                })

            # Setup DataFrame
            df = pd.DataFrame(merged)
            page_size = 10
            total_jobs = len(df)
            total_pages = (total_jobs - 1) // page_size + 1

            # Session-state page tracker
            if "job_page" not in st.session_state:
                st.session_state.job_page = 0

            # Pagination controls
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("◀️ Previous") and st.session_state.job_page > 0:
                    st.session_state.job_page -= 1
            with col3:
                if st.button("Next ▶️") and st.session_state.job_page < total_pages - 1:
                    st.session_state.job_page += 1
            with col2:
                st.markdown(
                    f"<div style='text-align:center;'>Page {st.session_state.job_page + 1} of {total_pages}</div>",
                    unsafe_allow_html=True
                )

            # Slice current page
            start_idx = st.session_state.job_page * page_size
            end_idx = start_idx + page_size
            st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True)

        except Exception as e:
            st.error(f"Failed to load or display jobs from S3: {e}")
        
    st.success(f"📊 Total Jobs: {len(jobs)}")



    # -- Contractor Trust Scores
    scores = compute_contractor_trust_scores()
    if scores:
        st.markdown("### 📊 Contractor Trust Scores")
        for cid, score in scores.items():
            st.markdown(f"**{cid}**: ⭐ {score}/5")

    st.success("🔗 All data fetched from S3 successfully.")


    st.header("📋 Live Incident Listing")
    from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
    from st_aggrid.shared import GridUpdateMode


    # ---------- Config ----------
    PER_PAGE = 10

    # ---------- Pagination ----------
    page = st.number_input("Incident Page", min_value=1, max_value=max(1, math.ceil(len(incidents)/PER_PAGE)), value=1)
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    paginated = incidents[start:end]

    if not paginated:
        st.warning("No incidents to display.")
        st.stop()

    # ---------- Build DataFrame ----------
    df = pd.DataFrame([{
        "Incident ID": i.get("incident_id"),
        "Issue": i.get("issue", "N/A"),
        "Priority": i.get("priority", "N/A"),
        "Created By": i.get("created_by", "N/A"),
        "Timestamp": i.get("chat_data", [{}])[-1].get("timestamp", "N/A"),
        "Summary": "🔍 View",
        "Export": "📄 Export",
        "Job": "➕ Job"
    } for i in paginated])

    # ---------- Configure Grid ----------
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(enabled=True)
    gb.configure_default_column(editable=False, groupable=False)

    for col in ["Summary", "Export", "Job"]:
        action = col
        gb.configure_column(action,
            cellRenderer=JsCode(f"""
                function(params) {{
                    const id = params.data["Incident ID"];
                    return `<span style='cursor:pointer;color:#1f77b4;text-decoration:underline;' onClick="streamlit.send({{type: 'streamlit:customEvent', detail: {{action: '{action.lower()}', id: id }} }})">${{params.value}}</span>`;
                }}
            """)
        )

    # ---------- AgGrid Render ----------
    AgGrid(
        df,
        gridOptions=gb.build(),
        height=400,
        update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True
    )
    
    clicked_payload = st.experimental_get_query_params().get("aggrid_click")
    if clicked_payload:
        try:
            detail = eval(clicked_payload[0])  # OR use json.loads if JSON encoded
            incident_dialog(detail["id"], detail["action"])
        except Exception as e:
            st.warning(f"Failed to parse click: {e}")

    # ---------- JS Listener to Trigger st.text_input (proxy method) ----------
    st.markdown("""
    <script>
    window.addEventListener('cellClick', function(e) {
        const payload = JSON.parse(e.detail);
        const input = window.parent.document.querySelector('iframe').contentWindow.document.querySelector('input[data-testid="stTextInput"][aria-label="cell_click"]');
        if (input) {
            input.value = payload.id + "::" + payload.action;
            input.dispatchEvent(new Event('input', { bubbles: true }));
        }
    });
    </script>
    """, unsafe_allow_html=True)

    # ---------- Hidden Input Trap ----------
    clicked = st.text_input("cell_click", key="clicked_cell", label_visibility="collapsed")

    # ---------- Dialog ----------
    @st.experimental_dialog("📄 Incident Action")
    def incident_dialog(incident_id, action):
        st.write(f"**Incident ID:** `{incident_id}`")
        st.write(f"**Action:** `{action}`")

        if action == "summary":
            # from ss5_summonengine.chat_summarizer import summarize_chat_thread
            st.error("🔍 Summary feature unavailable.")
        elif action == "export":
            from superstructures.ss7_intelprint.report_engine import generate_pdf_report
            try:
                path = generate_pdf_report(incident_id)
                st.success(f"✅ Report generated at: `{path}`")
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        st.download_button("⬇️ Download PDF", data=f, file_name=f"{incident_id}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"❌ Export error: {e}")
        elif action == "job":
            # from superstructures.ss6_actionrelay.job_manager import create_job
            st.error("➕ Job creation feature unavailable.")
        else:
            st.warning("⚠️ Unknown action.")

    # ---------- Trigger Dialog ----------
    if "::" in st.session_state.get("clicked_cell", ""):
        inc_id, action = st.session_state["clicked_cell"].split("::")
        incident_dialog(inc_id, action)
        st.session_state["clicked_cell"] = ""







    # -- Tenant Feedback History
    feedback_entries = load_all_feedback()

    # if "feedback" not in st.session_state:
    #     st.session_state["feedback"] = load_all_feedback()

    # all_feedback = st.session_state["feedback"]

    # # Example usage
    # st.markdown(f"### 📬 Total Feedback Received: {len(all_feedback)}")

    # for entry in all_feedback:
    #     with st.expander(f"Job ID: {entry['job_id']}"):
    #         st.write(f"Submitted by: {entry['submitted_by']}")
    #         st.write(f"Role: {entry['role']}")
    #         st.write(f"Rating: {entry['rating']}")
    #         st.write(f"Notes: {entry['notes']}")

    if feedback_entries:
        st.markdown("## 🗣️ Tenant Feedback History")
        for fb in feedback_entries:
            with st.expander(f"Job: {fb['job_id']} — ⭐ {fb['rating']}"):
                st.markdown(f"**Submitted by:** {fb['submitted_by']}")
                st.markdown(f"**Comment:** {fb['comment']}")
                st.caption(f"🕒 {fb['timestamp']}")
    else:
        st.info("No feedback submitted yet.")

    if st.button("🔍 Analyze Feedback"):
        from feedback_reflector import analyze_feedback
        summary = analyze_feedback()
        st.markdown("### 📊 GPT Feedback Summary")
        st.markdown(summary)

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
