import streamlit as st
from streamlit_elements import elements
import json
import os
from datetime import datetime
from uuid import uuid4

from superstructures.ss5_summonengine.summon_engine import run_summon_engine
from superstructures.ss7_mediastream import media_stream
from superstructures.ss8_canvascard import create_canvas_card

CHAT_LOG_PATH = "logs/chat_thread_main.json"

def run_chat_core():
    st.title("Tenant Chat Interface")
    st.subheader("TriChat – Unified Chat Interface")

    if "persona" not in st.session_state:
        st.session_state["persona"] = "tenant"
    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = str(uuid4())

    persona = st.session_state["persona"]
    thread_id = st.session_state["thread_id"]

    if not os.path.exists("logs"):
        os.makedirs("logs")

    try:
        with open(CHAT_LOG_PATH, "r") as f:
            chat_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        chat_log = []

    with st.expander("📸 Upload or Capture Media"):
        media_stream()

    st.markdown("#### 🧠 Suggested Smart Summary:")

    with elements("canvas"):
        create_canvas_card(
            title="Incident #123 – Leaking Pipe",
            content="Detected an incident: leaking pipe under kitchen sink reported by tenant.",
            actions=[
                {"label": "Create Job Ticket", "callback": lambda: st.success("✅ Job Ticket Created")},
                {"label": "Request More Info", "callback": lambda: st.info("ℹ️ Waiting for photo upload")}
            ]
        )

    st.markdown("---")

    with st.container():
        st.markdown(
            """
            <div style='height: 400px; overflow-y: auto; border: 1px solid #333; padding: 10px; background-color: #0f0f0f;'>
            """,
            unsafe_allow_html=True
        )
        for msg in chat_log:
            role = msg.get("role", "").capitalize()
            content = msg.get("message", "")
            st.markdown(f"<p style='margin-bottom: 6px;'><strong>{role}:</strong> {content}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Type a message...", key="chat_input")
        submitted = st.form_submit_button("Send")

    if submitted and user_input.strip():
        user_msg = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": persona,
            "message": user_input.strip()
        }
        chat_log.append(user_msg)

        try:
            agent_reply = run_summon_engine(chat_log, user_input.strip(), persona, thread_id)
        except Exception as e:
            agent_reply = f"[Agent error: {str(e)}]"

        if agent_reply:
            agent_msg = {
                "id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "role": "agent",
                "message": agent_reply
            }
            chat_log.append(agent_msg)

        with open(CHAT_LOG_PATH, "w") as f:
            json.dump(chat_log, f, indent=2)

        st.rerun()
