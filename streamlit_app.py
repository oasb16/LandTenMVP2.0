import streamlit as st
from superstructures.ss1_gate.streamlit_frontend.ss1_gate_app import run_login
from superstructures.ss1_gate.persona_extractor import extract_persona
from superstructures.ss1_gate.shared.dynamodb import save_user_profile
from streamlit_javascript import st_javascript
from datetime import datetime
import requests, logging, traceback
import base64
import json
import jwt
from websocket_server import log_error,log_success,log_popover

st.set_page_config(page_title="LandTen 2.0 – TriChatLite", layout="wide")

# === Secrets
try:
    COGNITO_DOMAIN = st.secrets["COGNITO_DOMAIN"]
    REDIRECT_URI = st.secrets["REDIRECT_URI"]
    CLIENT_ID = st.secrets["COGNITO_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["COGNITO_CLIENT_SECRET"]
    TOKEN_ENDPOINT = f"{COGNITO_DOMAIN}/oauth2/token"
except KeyError as e:
    st.error(f"Missing required secret: {e.args[0]}")
    st.stop()

from utils.session_persistence import try_restore_session, store_session

# Attempt to restore session before anything else
if "logged_in" not in st.session_state:
    try_restore_session()

# Define symbolic states
states = {
    "idle": "Agent is inactive",
    "engaged": "Agent is processing user input",
    "media_processing": "Agent is analyzing media",
    "completed": "Agent has completed processing"
}
st.session_state['agent_state'] = "idle"

# === Query param extraction
with st.sidebar:
    params = st.query_params
    if "code" in params:
        st.session_state["oauth_code"] = params["code"]
        st.popover(f"params[] : {params["code"]}")    
        st.session_state['persona'] = st.selectbox("Choose your role", ["tenant", "landlord", "contractor"])
        st.popover(f"Selected role: {st.session_state['persona']}")
        st.session_state["logged_in"] = True
        st.popover("Logged in successfully!")
        st.text(f"Agent state: {st.session_state['agent_state']}")
        st.text(f"Agent status: {states[st.session_state['agent_state']]}")

# === Routing helper
def handle_persona_routing():
    page_map = {
        "tenant": "tenant_dashboard",
        "contractor": "contractor_dashboard",
        "landlord": "landlord_dashboard"
    }
    page = page_map.get(st.session_state["persona"], None)
    st.success(f"Routing to {page} for persona {st.session_state['persona']}")
    if page:
        st.session_state["page"] = page
    else:
        st.error("Unknown persona. Please contact support.")

# === Logout
def logout():
    import streamlit.components.v1 as components
    components.html('<script>window.location.href = "https://landtenmvp20.streamlit.app/";</script>', height=0)

# === Init
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# === Login flow
if not st.session_state["logged_in"]:
    run_login()


# === Handle token
if "oauth_code" in st.session_state and "user_profile" not in st.session_state:
    code = st.session_state["oauth_code"]
    if st.session_state.get("last_code") == code:
        st.warning("⚠️ Duplicate login attempt. Refresh if stuck.")
        try_restore_session()
    st.session_state["last_code"] = code

    basic_auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {basic_auth}"
    }
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    try:
        res = requests.post(TOKEN_ENDPOINT, data=payload, headers=headers)
        if res.status_code == 200:
            tokens = res.json()
            id_token = tokens.get("id_token", "")
            user_info = jwt.decode(id_token, options={"verify_signature": False})

            st.session_state["user_profile"] = user_info
            st.session_state["email"] = user_info.get("email", "")
            st.session_state["logged_in"] = True
            if st.session_state["persona"] not in ["tenant", "landlord", "contractor"]:
                st.session_state["persona"] = extract_persona(user_info.get("cognito:groups", []))    
            st.session_state["persona"] = st.session_state.get("persona", "tenant")
            st.session_state["expires_at"] = user_info["exp"]

            # 🔐 Persist in browser
            store_session(user_info)

            try:
                save_user_profile({
                    "user_id": user_info.get("userId", ""),
                    "name": user_info.get("cognito:username", ""),
                    "email": user_info.get("email", ""),
                    "persona": st.session_state['persona'],
                    "login_source": "GoogleSSO",
                    "timestamp": datetime.utcnow().isoformat()
                })
                st.success("✅ Profile saved to DB")
                st.success(f"Welcome, {user_info.get('cognito:username', 'User')}! You are logged in as {st.session_state['persona']}.")
                st.success(f"Your email: {user_info.get('email', 'Unknown')}")
                st.success(f"Your user ID: {user_info.get('userId', 'Unknown')}")
                st.success(f"Your session expires at: {datetime.fromtimestamp(user_info['exp'])}")
                st.success(f"Your persona: {st.session_state['persona']}")
            except Exception as e:
                st.error(f"DB write failed: {e}")

            import streamlit.components.v1 as components
            components.html(f"""
                <script>
                localStorage.setItem("user_profile", JSON.stringify({json.dumps(st.session_state["user_profile"])}));
                localStorage.setItem("expires_at", {user_info["exp"]});
                </script>
            """, height=0)

            # st.rerun()
        else:
            st.error(f"OAuth token request failed: {res.status_code} {res.text}")
    except Exception as e:
        st.error(f"Token exchange error: {e}")

# === Routing
if "user_profile" in st.session_state:
    handle_persona_routing()

if st.session_state.get("logged_in") and "page" not in st.session_state:
    handle_persona_routing()

page = st.session_state.get("page")
if not page:
    st.error("No page specified. Please log in again.")
    st.stop()

# === Final route
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