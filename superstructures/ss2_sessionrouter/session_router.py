import streamlit as st
import uuid

def run_session_router():
    # Role set from query param or default
    if "role" not in st.session_state:
        role = st.experimental_get_query_params().get("role", ["tenant"])[0].lower()
        st.session_state["role"] = role

    # Thread ID for logging
    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = str(uuid.uuid4())

    role = st.session_state["role"]
    thread_id = st.session_state["thread_id"]

    # Sidebar info
    st.sidebar.markdown(f"**Current Role:** `{role}`")
    st.sidebar.markdown(f"**Thread ID:** `{thread_id}`")

    # View injection map (no role if-else)
    view_dispatch = {
        "tenant": lambda: st.markdown("🎒 Tenant view loaded. You can raise issues."),
        "landlord": lambda: st.markdown("🏠 Landlord view loaded. You can approve/decline."),
        "contractor": lambda: st.markdown("🛠️ Contractor view loaded. You can bid/complete.")
    }

    view_dispatch.get(role, lambda: st.warning("Unknown role"))()