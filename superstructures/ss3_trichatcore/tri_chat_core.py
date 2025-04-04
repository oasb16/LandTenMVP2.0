import streamlit as st
import json
import os
from datetime import datetime
from uuid import uuid4

from superstructures.ss5_summonengine.summon_engine import run_summon_engine

CHAT_LOG_PATH = "logs/chat_thread_main.json"

def run_chat_core():
    st.title("Tenant Chat Interface")
    st.subheader("TriChat – Unified Chat Interface")

    if "persona" not in st.session_state or "thread_id" not in st.session_state:
        st.warning("⚠️ No role selected. Please log in via PersonaGate.")
        return

    persona = st.session_state["persona"]
    thread_id = st.session_state["thread_id"]

    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Load chat history
    try:
        with open(CHAT_LOG_PATH, "r") as f:
            chat_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        chat_log = []

    # Display chat history
    role_emoji = {
        "tenant": "🧑 Tenant",
        "assistant": "🤖 GPT",
        "landlord": "🧑‍💼 Landlord",
        "contractor": "🛠️ Contractor"
    }

    for msg in chat_log:
        role = msg.get("role", "")
        content = msg.get("message", "")
        emoji = role_emoji.get(role, "❓")
        st.markdown(f"**{emoji}:** {content}")

    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Type a message...", key="chat_input")
        submitted = st.form_submit_button("Send")

    if submitted and user_input.strip():
        # Save user message
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
            agent_reply = f"[⚠️ GPT error: {e}]"

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
