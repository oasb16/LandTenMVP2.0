import streamlit as st
from superstructures.ss1_gate.streamlit_frontend.ss1_gate_app import run_login
from superstructures.ss1_gate.persona_extractor import extract_persona
# from superstructures.ss1_gate.shared.dynamodb import save_user_profile
from superstructures.ss2_pulse.ss2_pulse_app import run_router
from uuid import uuid4
from datetime import datetime
import logging

# Verify secrets configuration
try:
    CLIENT_ID = st.secrets["COGNITO_CLIENT_ID"]
    REDIRECT_URI = "https://landtenmvp20.streamlit.app/"
    COGNITO_DOMAIN = "https://us-east-1liycxnadt.auth.us-east-1.amazoncognito.com"
except KeyError as e:
    st.error(f"Missing required secret: {e.args[0]}")
    st.stop()

# Function to handle persona-based routing
def handle_persona_routing():
    st.success("Login successful! Redirecting...")
    persona = extract_persona()
    st.session_state["persona"] = persona
    if persona == "tenant":
        st.query_params(page="tenant_dashboard")
        st.rerun()
    elif persona == "contractor":
        st.query_params(page="contractor_dashboard")
        st.rerun()
    elif persona == "landlord":
        st.query_params(page="landlord_dashboard")
        st.rerun()
    else:
        st.error("Unknown persona. Please contact support.")

# Main application logic
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    run_login()
    if "user_profile" in st.session_state:
        # save_user_profile(st.session_state["user_profile"])
        handle_persona_routing()
else:
    # Route to the appropriate persona page
    page = st.query_params.get("page", [None])[0]

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