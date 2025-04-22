import streamlit as st

# -- SS1: Login (Google SSO via Cognito)
from superstructures.ss1_gate.streamlit_frontend.ss1_gate_app import run_login

# -- SS2: Persona router
from superstructures.ss2_pulse.ss2_pulse_app import run_router

# -- SS3: Chat core
from superstructures.ss3_trichatcore.tri_chat_core import run_chat_core

# -- Optional logout logic in sidebar
from urllib.parse import quote

# Verify secrets configuration
try:
    CLIENT_ID = st.secrets["COGNITO_CLIENT_ID"]
    REDIRECT_URI = "https://landtenmvp20.streamlit.app/"
    COGNITO_DOMAIN = "https://us-east-1liycxnadt.auth.us-east-1.amazoncognito.com"
except KeyError as e:
    st.error(f"Missing required secret: {e.args[0]}")
    st.stop()

# -- App UI setup
st.set_page_config(page_title="LandTen 2.0 – TriChatLite", layout="wide")

# -- Sidebar logout
if st.session_state.get("logged_in"):
    st.sidebar.markdown(f"👤 **{st.session_state.get('email', 'Unknown')}**")
    if st.sidebar.button("Logout"):
        try:
            logout_url = (
                f"{COGNITO_DOMAIN}/logout?"
                f"client_id={CLIENT_ID}&"
                f"logout_uri={REDIRECT_URI}"
            )
            st.session_state.clear()
            st.markdown(f"[🔓 Logged out — click to re-login]({logout_url})")
            st.stop()
        except Exception as e:
            st.error(f"Error during logout: {str(e)}")

# -- Route user
if not st.session_state.get("logged_in"):
    run_login()
else:
    persona = st.session_state.get("persona", "tenant")

    if persona == "tenant":
        st.title("Tenant Dashboard")
        run_chat_core()
    elif persona == "landlord":
        st.title("Landlord Dashboard")
        run_chat_core()
    elif persona == "contractor":
        st.title("Contractor Dashboard")
        run_chat_core()
    else:
        st.error("Invalid persona. Please contact support.")
