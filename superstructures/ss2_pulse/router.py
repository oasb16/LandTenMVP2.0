import streamlit as st

# Chat-first architecture modules (TriChatLite)
from superstructures.ss3_trichatcore.tri_chat_core import run_chat_core
from superstructures.ss4_agenttoggle.agent_toggle_ui import run_agent_toggle
from superstructures.ss5_summonengine.summon_engine import run_summon_engine
from superstructures.ss6_actionrelay.actionrelay import run_action_relay

# Optional: admin view
from superstructures.tracker import show_tracker


def route_user(persona: str):

    # 🔁 Ensure TriChatLite compatibility (legacy modules use "role", not "persona")
    if "persona" in st.session_state and "role" not in st.session_state:
        st.session_state["role"] = st.session_state["persona"]


    if persona == "tenant":
        st.title("LandTenMVP2.0")
        run_chat_core()
        run_agent_toggle()
        try:
            # 🔁 Prepare arguments for GPT summon
            chat_history = st.session_state.get("chat_log", [])
            user_input = st.session_state.get("last_user_message", "")
            persona = st.session_state.get("role", "tenant")
            thread_id = st.session_state.get("thread_id", "undefined-thread")
            # 🔮 Call summon engine with full context
            run_summon_engine(chat_history, user_input, persona, thread_id)
            # 🛡️ Run ActionRelay with full symbolic state
            # 🔁 Loop over all messages and inject action buttons if eligible
            for message in chat_history:
                msg_id = message.get("id", "unknown-msg")
                run_action_relay(message, msg_id)
        except Exception as e:
            st.error(f"Summon Engine Error: {type(e).__name__} – {e}")


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
