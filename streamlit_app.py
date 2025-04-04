import streamlit as st

# -- SS1: Login (Google SSO via Cognito)
from superstructures.ss1_gate.streamlit_frontend.ss1_gate_app import run_login

# -- SS2: Persona router
from superstructures.ss2_pulse.ss2_pulse_app import run_router

# -- Optional logout logic in sidebar
from urllib.parse import quote

COGNITO_DOMAIN = "https://us-east-1liycxnadt.auth.us-east-1.amazoncognito.com"
CLIENT_ID = st.secrets.get("COGNITO_CLIENT_ID")
REDIRECT_URI = "https://landtenmvp20.streamlit.app/"

# -- App UI setup
st.set_page_config(page_title="LandTen 2.0 – TriChatLite", layout="wide")

# -- Sidebar logout
if st.session_state.get("logged_in"):
    st.sidebar.markdown(f"👤 **{st.session_state.get('email', 'Unknown')}**")
    if st.sidebar.button("Logout"):
        logout_url = (
            f"{COGNITO_DOMAIN}/logout?"
            f"client_id={CLIENT_ID}&"
            f"logout_uri={REDIRECT_URI}"
        )
        st.session_state.clear()
        st.markdown(f"[🔓 Logged out — click to re-login]({logout_url})")
        st.stop()

# -- Route user
if not st.session_state.get("logged_in"):
    run_login()
else:
    run_router()
