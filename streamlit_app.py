import streamlit as st
from streamlit.components.v1 import html

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

# -- Sidebar
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.get('email', 'Unknown')}**")
    if st.button("Logout"):
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

# -- Main Layout
persona = st.session_state.get("persona", "tenant")

st.title(f"{persona.capitalize()} Dashboard")

# Split layout into two halves
col1, col2 = st.columns([2, 3])

# Left column: Chat window
with col1:
    st.subheader("Chat Window")
    run_chat_core()

# Right column: Persona-specific container
with col2:
    st.subheader("Details")
    if persona == "tenant":
        st.markdown("### Incidents")
        st.markdown("<div style='height: 200px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;'>Incident details will appear here.</div>", unsafe_allow_html=True)
    elif persona == "landlord":
        st.markdown("### Jobs")
        st.markdown("<div style='height: 200px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;'>Job details will appear here.</div>", unsafe_allow_html=True)
    elif persona == "contractor":
        st.markdown("### Jobs and Schedule")
        st.markdown("<div style='height: 100px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;'>Job details will appear here.</div>", unsafe_allow_html=True)
        st.markdown("<div style='height: 100px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;'>Schedule details will appear here.</div>", unsafe_allow_html=True)
    else:
        st.error("Invalid persona. Please contact support.")

# -- Mobile Compatibility
html("<style>@media (max-width: 768px) { .css-1lcbmhc { flex-direction: column; } }</style>")
