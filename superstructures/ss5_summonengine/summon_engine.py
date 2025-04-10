import streamlit as st
import os
import json
from datetime import datetime
from uuid import uuid4
from utils.gpt_call import call_gpt_agent

def run_summon_engine(chat_log, user_input, persona, thread_id):
    if not st.session_state.get("agent_active", True):
        return "[Agent inactive]"

    # Optional live feedback UI
    with st.spinner("🤖 Agent is thinking..."):
        try:
            reply = call_gpt_agent(chat_log)
        except Exception as e:
            return f"[GPT Error: {e}]"

    # Save to log
    response_msg = {
        "id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "role": "agent",
        "message": reply,
        "thread_id": thread_id,
        "persona_context": persona
    }

    chat_log.append(response_msg)

    # Persist chat log
    os.makedirs("logs", exist_ok=True)
    with open("logs/chat_thread_main.json", "w") as f:
        json.dump(chat_log, f, indent=2)

    return reply
