# test_trichat_happy_path.py

import sys
import os
# Add the root of the project to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from datetime import datetime
from uuid import uuid4

from superstructures.ss5_summonengine.summon_engine import run_summon_engine

st.title("✅ TriChat Happy Path Test")

# Simulate a minimal user chat log
chat_log = [
    {
        "id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "role": "tenant",
        "message": "There's water leaking under the sink."
    }
]

user_input = chat_log[-1]["message"]
persona = "tenant"
thread_id = str(uuid4())

st.markdown(f"**Simulated User Input:** `{user_input}`")

# Run GPT logic
if st.button("Run Summon Engine"):
    try:
        reply = run_summon_engine(chat_log, user_input, persona, thread_id)
        st.success("✅ GPT Agent Response:")
        st.markdown(reply)
    except Exception as e:
        st.error(f"❌ Error: {e}")
