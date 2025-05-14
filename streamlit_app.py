import streamlit as st
from superstructures.ss1_gate.streamlit_frontend.ss1_gate_app import run_login
from superstructures.ss1_gate.persona_extractor import extract_persona
from datetime import datetime

st.set_page_config(page_title="LandTen 2.0 – TriChatLite", layout="wide")  # MUST be first

# === Config Check ===
try:
    CLIENT_ID = st.secrets["COGNITO_CLIENT_ID"]
    REDIRECT_URI = st.secrets["REDIRECT_URI"]
    COGNITO_DOMAIN = st.secrets["COGNITO_DOMAIN"]
except KeyError as e:
    st.error(f"Missing required secret: {e.args[0]}")
    st.stop()

# ✅ Proper query param extraction using new API (READ ONLY)
params = st.query_params
if "code" in params:
    st.session_state["oauth_code"] = params["code"][0]
    st.session_state["oauth_state"] = params.get("state", [""])[0]
    st.success(f"OAuth code: {st.session_state['oauth_code']}")
    st.success(f"OAuth state: {st.session_state['oauth_state']}")

    # ✅ Simulate "clearing" by redirecting to same page with clean URL
    st.markdown(
        """
        <meta http-equiv="refresh" content="0; url='/'" />
        """,
        unsafe_allow_html=True
    )
    st.stop()

# === Utility: Persona → Page Router
def handle_persona_routing():

    page_map = {
        "tenant": "tenant_dashboard",
        "contractor": "contractor_dashboard",
        "landlord": "landlord_dashboard"
    }
    page = page_map.get(st.session_state["persona"], "none")
    st.success(f"Decoded persona: {st.session_state['persona']}")
    st.success(f"Page mapping: {page_map}")
    st.success(f"Page: {page}")
    if page:
        st.session_state["page"] = page
        # st.rerun()
    else:
        st.error("Unknown persona. Please contact support.")

# === Utility: Logout Handler
def logout():
    for key in ["logged_in", "user_profile", "persona", "page"]:
        st.session_state.pop(key, None)
    st.rerun()

# === Init Session State
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.success("Welcome to LandTen MVP 2.0! Please log in.")
    if 'oauth_code' in st.session_state:
        st.success(f"OAuth code: {st.session_state['oauth_code']}")
    if 'oauth_state' in st.session_state:
        st.success(f"OAuth state: {st.session_state['oauth_state']}")
    else:
        st.success(f"session_state: {st.session_state}")

# === LOGIN FLOW
if not st.session_state["logged_in"]:
    st.success(f"Before run_login st.session_state: {st.session_state}")
    run_login()
    st.success(f"After run_login st.session_state: {st.session_state}")
    if "user_profile" in st.session_state:
        st.session_state["logged_in"] = True
        handle_persona_routing()
    else:
        st.error("Login failed. Please try again.")
        # st.stop()

# === Fallback Recovery
if st.session_state.get("logged_in") and "page" not in st.session_state:
    handle_persona_routing()


# === Page Routing
page = st.session_state.get("page")
if page is None:
    st.error("No page specified. Please log in again.")
    # st.stop()

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
