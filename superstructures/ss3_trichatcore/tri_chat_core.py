import streamlit as st
import json
import os
from datetime import datetime
from uuid import uuid4

from superstructures.ss5_summonengine.summon_engine import run_summon_engine
from superstructures.ss7_mediastream import media_stream
from superstructures.ss8_canvascard import create_canvas_card

CHAT_LOG_PATH = "logs/chat_thread_main.json"


def chat_interface():
    st.title("LandTen Chat Interface")
    media_stream()
    # Example usage of create_canvas_card
    create_canvas_card(
        title="Incident #123",
        content="Leaking pipe in the kitchen.",
        actions=[
            {"label": "Approve", "callback": lambda: st.write("Approved!")},
            {"label": "Request Info", "callback": lambda: st.write("Info Requested.")}
        ]
    )
    # Chat messages and other UI components go here


def run_chat_core():
    st.title("Tenant Chat Interface")
    st.subheader("TriChat – Unified Chat Interface")

    if "persona" not in st.session_state or "thread_id" not in st.session_state:
        st.warning("⚠️ No role selected. Please log in via PersonaGate.")
        st.session_state["persona"] = "tenant"
        st.session_state["thread_id"] = "123"
        # return

    persona = st.session_state["persona"]
    thread_id = st.session_state["thread_id"]

    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Load existing chat
    try:
        with open(CHAT_LOG_PATH, "r") as f:
            chat_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        chat_log = []

    # Chat display box
    with st.container():
        st.markdown(
            """
            <div style='height: 400px; overflow-y: auto; border: 1px solid #444; padding: 10px; background-color: #111;'>
            """,
            unsafe_allow_html=True
        )
        for msg in chat_log:
            role = msg.get("role", "").capitalize()
            content = msg.get("message", "")
            st.markdown(f"<p style='margin: 0;'><strong>{role}:</strong> {content}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Chat input form
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Type a message...", key="chat_input")
        submitted = st.form_submit_button("Send")

    if submitted and user_input.strip():
        # Save user input
        new_msg = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": persona,
            "message": user_input.strip()
        }
        chat_log.append(new_msg)

        # GPT response
        try:
            agent_reply = run_summon_engine(chat_log, user_input.strip(), persona, thread_id)
        except Exception as e:
            agent_reply = f"[GPT error: {str(e)}]"

        if agent_reply:
            chat_log.append({
                "id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "role": "assistant",
                "message": agent_reply
            })

        with open(CHAT_LOG_PATH, "w") as f:
            json.dump(chat_log, f, indent=2)

        st.rerun()
