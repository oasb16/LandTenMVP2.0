import streamlit as st
from superstructures.ss1_personagate.personagate import run_persona_gate
from superstructures.ss2_sessionrouter.session_router import run_session_router
from superstructures.ss3_trichatcore.tri_chat_core import run_chat_core
from superstructures.ss4_agenttoggle.agent_toggle_ui import run_agent_toggle
from superstructures.ss5_summonengine.summon_engine import run_summon_engine
from superstructures.ss6_actionrelay.actionrelay import run_action_relay

st.set_page_config(page_title="TriChatLite", layout="wide")

if "role" not in st.session_state:
    run_persona_gate()
else:
    run_session_router()
    run_chat_core()
    run_agent_toggle()
    run_summon_engine()
    run_action_relay()
