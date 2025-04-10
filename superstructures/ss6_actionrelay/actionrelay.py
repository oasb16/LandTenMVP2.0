import streamlit as st
import json
import os
from datetime import datetime


def render_actions(actions):
    for action in actions:
        if action['visible_to'] == st.session_state["role"]:
            if st.button(action['label']):
                action['callback']()

def run_action_relay(message_block: dict, message_id: str):
    role = st.session_state.get("role", "tenant")
    session_id = st.session_state.get("session_uuid", "unknown-session")

    visible_actions = [
        a for a in message_block.get("actions", [])
        if a.get("visible_to") == role
    ]

    for action in visible_actions:
        if st.button(action["label"], key=f"{message_id}_{action['label']}"):
            _append_to_chat_history(role, action["label"])
            _log_action(session_id, message_id, action["label"], role)

def _append_to_chat_history(role, label):
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    st.session_state.chat_history.append({
        "sender": "system",
        "message": f"{role.capitalize()} selected: {label}",
        "timestamp": datetime.utcnow().isoformat()
    })

def _log_action(session_id, message_id, label, role):
    os.makedirs("logs", exist_ok=True)
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "role": role,
        "message_id": message_id,
        "action": label
    }
    with open("logs/action_log.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
