
import streamlit as st
import json
import os
from datetime import datetime
from uuid import uuid4
from utils.gpt_call import call_gpt_agent

def run_summon_engine(chat_log, user_input, persona, thread_id):
    if not st.session_state.get("agent_active", False):
        return

    st.info("🤖 Agent analyzing...")

    # Get GPT reply
    reply = call_gpt_agent(chat_log)

    # Append reply to log
    chat_log.append({
        "id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "role": "agent",
        "message": reply
    })

    # Persist log
    if not os.path.exists("logs"):
        os.makedirs("logs")
    with open("logs/chat_thread_main.json", "w") as f:
        json.dump(chat_log, f, indent=2)

    st.success("💡 Agent replied.")
