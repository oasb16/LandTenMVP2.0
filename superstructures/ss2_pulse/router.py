import streamlit as st

# Chat-first architecture modules (TriChatLite)
from superstructures.ss3_trichatcore.tri_chat_core import run_chat_core
from superstructures.ss4_agenttoggle.agent_toggle_ui import run_agent_toggle
from superstructures.ss5_summonengine.summon_engine import run_summon_engine
from superstructures.ss6_actionrelay.actionrelay import run_action_relay

# Optional: admin view
from superstructures.tracker import show_tracker

# Feature-specific modules
from superstructures.ss9_maintenance_requests import handle_maintenance_requests
from superstructures.ss10_task_assignment import assign_tasks_to_contractors
from superstructures.ss11_performance_dashboard import show_performance_dashboard
from superstructures.ss12_ai_suggestions import show_ai_suggestions
from superstructures.ss13_real_time_communication import handle_real_time_communication
from superstructures.ss14_interactive_extensions import show_interactive_extensions

def route_user(persona: str):

    # 🔁 Ensure TriChatLite compatibility (legacy modules use "role", not "persona")
    if "persona" in st.session_state and "role" not in st.session_state:
        st.session_state["role"] = st.session_state["persona"]


    if persona == "tenant":
        st.title("Tenant Dashboard")
        st.subheader("📋 Manage Your Rental Experience")
        st.button("Submit Maintenance Request", on_click=lambda: st.session_state.update({"action": "submit_request"}))
        st.button("View Rent Payment History", on_click=lambda: st.session_state.update({"action": "view_payments"}))
        st.button("Contact Landlord", on_click=lambda: st.session_state.update({"action": "contact_landlord"}))
        st.info("💡 Tip: Use the chat to ask questions or report issues directly.")

        if st.session_state.get("action") == "submit_request":
            handle_maintenance_requests()

        try:
            chat_history = st.session_state.get("chat_log", [])
            user_input = st.session_state.get("last_user_message", "")
            persona = st.session_state.get("role", "tenant")
            thread_id = st.session_state.get("thread_id", "undefined-thread")
            run_summon_engine(chat_history, user_input, persona, thread_id)
            for message in chat_history:
                msg_id = message.get("id", "unknown-msg")
                run_action_relay(message, msg_id)
        except Exception as e:
            st.error(f"Summon Engine Error: {type(e).__name__} – {e}")


    elif persona == "landlord":
        st.title("Landlord Dashboard")
        st.subheader("🏠 Manage Properties and Tenants")
        st.button("Assign Tasks to Contractors", on_click=lambda: st.session_state.update({"action": "assign_tasks"}))
        st.button("View Property Performance", on_click=lambda: st.session_state.update({"action": "view_performance"}))
        st.button("AI-Driven Suggestions", on_click=lambda: st.session_state.update({"action": "ai_suggested_actions"}))
        st.button("Real-Time Communication", on_click=lambda: st.session_state.update({"action": "real_time_communication"}))
        st.button("Interactive Extensions", on_click=lambda: st.session_state.update({"action": "interactive_extensions"}))
        st.info("💡 Tip: Use the dashboard to assign tasks and monitor property performance.")

        if st.session_state.get("action") == "assign_tasks":
            assign_tasks_to_contractors()

        if st.session_state.get("action") == "view_performance":
            show_performance_dashboard()

        if st.session_state.get("action") == "ai_suggested_actions":
            show_ai_suggestions()

        if st.session_state.get("action") == "real_time_communication":
            handle_real_time_communication()

        if st.session_state.get("action") == "interactive_extensions":
            show_interactive_extensions()

        try:
            chat_history = st.session_state.get("chat_log", [])
            user_input = st.session_state.get("last_user_message", "")
            persona = st.session_state.get("role", "landlord")
            thread_id = st.session_state.get("thread_id", "undefined-thread")
            run_summon_engine(chat_history, user_input, persona, thread_id)
            for message in chat_history:
                msg_id = message.get("id", "unknown-msg")
                run_action_relay(message, msg_id)
        except Exception as e:
            st.error(f"Summon Engine Error: {type(e).__name__} – {e}")

    elif persona == "contractor":
        st.title("Contractor Dashboard")
        st.subheader("🔧 Manage Assigned Tasks")
        st.button("View Assigned Tasks", on_click=lambda: st.session_state.update({"action": "view_tasks"}))
        st.button("Update Task Status", on_click=lambda: st.session_state.update({"action": "update_status"}))
        st.button("Contact Landlord or Tenant", on_click=lambda: st.session_state.update({"action": "contact"}))
        st.info("💡 Tip: Use the chat to get task details or report progress.")

        try:
            chat_history = st.session_state.get("chat_log", [])
            user_input = st.session_state.get("last_user_message", "")
            persona = st.session_state.get("role", "contractor")
            thread_id = st.session_state.get("thread_id", "undefined-thread")
            run_summon_engine(chat_history, user_input, persona, thread_id)
            for message in chat_history:
                msg_id = message.get("id", "unknown-msg")
                run_action_relay(message, msg_id)
        except Exception as e:
            st.error(f"Summon Engine Error: {type(e).__name__} – {e}")

    elif persona == "admin":
        st.title("Admin Dashboard")
        st.subheader("🔍 Monitor Platform Activities")
        show_tracker()
        st.info("💡 Tip: Use the tracker to view system logs and user activities.")

    else:
        st.error("❌ Invalid persona.")
