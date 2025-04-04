import streamlit as st

# Chat-first architecture modules (TriChatLite)
from superstructures.ss3_trichatcore.tri_chat_core import run_chat_core
from superstructures.ss4_agenttoggle.agent_toggle_ui import run_agent_toggle
from superstructures.ss5_summonengine.summon_engine import run_summon_engine
from superstructures.ss6_actionrelay.actionrelay import run_action_relay

# Optional: admin view
from superstructures.tracker import show_tracker


def route_user(persona: str):
    if persona == "tenant":
        st.title("Tenant Chat Interface")
        run_chat_core()
        run_agent_toggle()
        run_summon_engine()
        run_action_relay()

    elif persona == "landlord":
        st.title("Landlord Dashboard")
        st.info("🚧 Landlord view is under construction.")

    elif persona == "contractor":
        st.title("Contractor Dashboard")
        st.info("🚧 Contractor view is under construction.")

    elif persona == "admin":
        show_tracker()

    else:
        st.error("❌ Invalid persona.")
