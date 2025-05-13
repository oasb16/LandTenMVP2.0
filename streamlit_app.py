import streamlit as st
from superstructures.ss1_gate.streamlit_frontend.ss1_gate_app import run_login
from superstructures.ss1_gate.persona_extractor import extract_persona
# from superstructures.ss1_gate.shared.dynamodb import save_user_profile
# from superstructures.ss2_pulse.ss2_pulse_app import run_router
from uuid import uuid4
from datetime import datetime
import logging

# === Config Check ===
try:
    CLIENT_ID = st.secrets["COGNITO_CLIENT_ID"]
    REDIRECT_URI = "https://landtenmvp20.streamlit.app/"
    COGNITO_DOMAIN = "https://us-east-1liycxnadt.auth.us-east-1.amazoncognito.com"
except KeyError as e:
    st.error(f"Missing required secret: {e.args[0]}")
    st.stop()

# === Utility: Route by persona
def handle_persona_routing():
    persona = extract_persona()
    st.session_state["persona"] = persona

    page_map = {
        "tenant": "tenant_dashboard",
        "contractor": "contractor_dashboard",
        "landlord": "landlord_dashboard"
    }

    page = page_map.get(persona)
    if page:
        st.session_state["page"] = page
        st.rerun()
    else:
        st.error("Unknown persona. Please contact support.")

# === Utility: Logout handler
def logout():
    for key in ["logged_in", "user_profile", "persona", "page"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# === Clear garbage from redirect (e.g., ?code=xyz)
if "code" in st.query_params or "state" in st.query_params:
    st.query_params.clear()
    st.rerun()

# === Session Init
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.success("Welcome to LandTen MVP 2.0! Please log in.")

# === Login flow
if not st.session_state["logged_in"]:
    st.success(f"Before run_login st.session_state: {st.session_state}")
    run_login()
    st.success(f"After run_login st.session_state: {st.session_state}")
    if "user_profile" in st.session_state:
        st.session_state["logged_in"] = True
        handle_persona_routing()
    else:
        st.stop()

# === Recovery routing after redirect / rerun
if st.session_state.get("logged_in") and "page" not in st.session_state:
    handle_persona_routing()

# === Routing
page = st.session_state.get("page", None)

if page is None:
    st.error("No page specified. Please log in again.")
    st.stop()

# === Dashboard Routes
if page == "tenant_dashboard":
    from superstructures.ss1_gate.streamlit_frontend.tenant_dashboard import run_tenant_dashboard
    run_tenant_dashboard()

elif page == "contractor_dashboard":
    from superstructures.ss1_gate.streamlit_frontend.contractor_dashboard import run_contractor_dashboard
    run_contractor_dashboard()

elif page == "landlord_dashboard":
    from superstructures.ss1_gate.streamlit_frontend.landlord_dashboard import run_landlord_dashboard
    run_landlord_dashboard()

else:
    st.error("Invalid page. Please log in again.")
