import streamlit as st
import json
import os
from datetime import datetime
from uuid import uuid4

CHAT_LOG_PATH = "logs/chat_thread_main.json"

def run_chat_core():
    st.title("TriChat – Unified Chat Interface")

    if "role" not in st.session_state:
        st.warning("No role selected. Please log in via PersonaGate.")
        return

    if not os.path.exists("logs"):
        os.makedirs("logs")

    try:
        with open(CHAT_LOG_PATH, "r") as f:
            chat_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        chat_log = []

    for msg in chat_log:
        role = msg.get("role", "unknown")
        content = msg.get("message", "")
        st.markdown(f"**{role.capitalize()}**: {content}")

    user_input = st.text_input("Type a message:", key="chat_input")
    if st.button("Send") and user_input.strip():
        new_message = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": st.session_state["role"],
            "message": user_input.strip()
        }
        chat_log.append(new_message)
        with open(CHAT_LOG_PATH, "w") as f:
            json.dump(chat_log, f, indent=2)
        st.experimental_rerun()
