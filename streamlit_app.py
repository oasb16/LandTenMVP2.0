import streamlit as st
from superstructures.ss1_gate.streamlit_frontend.ss1_gate_app import run_login
from superstructures.ss1_gate.persona_extractor import extract_persona
from datetime import datetime
import requests
import base64
import json
from datetime import datetime
import jwt
from urllib.parse import quote, unquote
from superstructures.ss1_gate.shared.dynamodb import save_user_profile

st.set_page_config(page_title="LandTen 2.0 – TriChatLite", layout="wide")  # MUST be first

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
st.success(f"Query params: {params}")
if "code" in params:
    st.session_state["oauth_code"] = params["code"]
    # state_raw = params.get("state", [""])[0]
    # st.session_state["oauth_state"] = state_raw

    # try:
    #     decoded_state = json.loads(unquote(state_raw))
    #     persona = decoded_state.get("persona", None)
    #     if persona:
    #         st.session_state["persona"] = persona
    #         st.success(f"✅ Persona restored from state: {persona}")
    #     else:
    #         st.warning("⚠️ Persona missing in state. Defaulting to 'tenant'.")
    #         st.session_state["persona"] = "tenant"
    # except Exception as e:
    #     st.error(f"❌ Failed to decode state param: {e}")
    #     st.session_state["persona"] = "tenant"

    # Step 1: Role Picker
    
    st.session_state['persona'] = st.selectbox("Choose your role", ["tenant", "landlord", "contractor"])
    st.success(f"Selected role: {st.session_state['persona']}") 

    st.session_state["logged_in"] = True
    st.success("Logged in successfully!")

    # ✅ Simulate "clearing" by redirecting to same page with clean URL
    # st.markdown(
    #     """
    #     <meta http-equiv="refresh" content="0; url='/'" />
    #     """,
    #     unsafe_allow_html=True
    # )
    # st.stop()

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
    with st.expander("### session_state", expanded=False):
        st.success(f"st.session_state: {st.session_state}")
    with st.expander("### user_profile", expanded=False):
        if st.session_state['user_profile']:
            st.success(f"st.session_state['user_profile']: {st.session_state['user_profile']}")
            st.success(f"Email: {st.session_state['user_profile']['email']}")
            st.success(f"Cognito Username: {st.session_state['user_profile']['cognito:username']}")
            st.success(f"Groups: {st.session_state['user_profile'].get('cognito:groups', [])}")
            st.success(f"Email Verified: {st.session_state['user_profile']['email_verified']}")
            st.success(f"Issuer: {st.session_state['user_profile']['iss']}")
            st.success(f"AUDIENCE: {st.session_state['user_profile']['aud']}")
            st.success(f"Token Use: {st.session_state['user_profile']['token_use']}")
            st.success(f"Issued At (iat): {st.session_state['user_profile']['iat']}")
            st.success(f"Expires At (exp): {st.session_state['user_profile']['exp']}")
            st.success(f"Auth Time: {st.session_state['user_profile']['auth_time']}")
            st.success(f"JWT ID: {st.session_state['user_profile']['jti']}")
            st.success(f"Origin JTI: {st.session_state['user_profile']['origin_jti']}")
            st.success(f"at_hash: {st.session_state['user_profile']['at_hash']}")
            st.success(f"User ID (from identity): {st.session_state['user_profile']['identities'][0]['userId']}")
            st.success(f"Provider: {st.session_state['user_profile']['identities'][0]['providerName']}")
            st.success(f"Login Source: GoogleSSO")
            st.success(f"Timestamp: {datetime.utcnow().isoformat()}")
        else:
            st.error("User profile not found in session state.")
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

# === LOGIN FLOW
if not st.session_state["logged_in"]:
    # st.success(f"Before run_login st.session_state: {st.session_state}")
    run_login()
    st.success(f"After run_login st.session_state: {st.session_state}")

# Handle token exchange
if st.session_state["oauth_code"]:
    code = st.session_state["oauth_code"]
    if st.session_state.get("last_code") == code:
        st.warning("⚠️ Duplicate login attempt. Refresh if stuck.")
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

            st.session_state["logged_in"] = True
            st.session_state["email"] = user_info.get("email", "")
            st.session_state["user_profile"] = user_info  # Now it exists!
            
            try:
                save_user_profile({
                    "user_id": user_info.get("userId", ""),
                    "name": user_info.get("cognito:username", ""),
                    "email": user_info.get("email", ""),
                    "persona": st.session_state['persona'],
                    "login_source": "GoogleSSO",
                    "timestamp": datetime.utcnow().isoformat()
                })
                st.success("User profile written to DB successfully.")
            except Exception as db_error:
                st.error(f"DB write failed: {db_error}")

            # st.rerun()

        else:
            st.error(f"OAuth token request failed: {res.status_code} {res.text}")
    except Exception as e:
        st.error(f"Token exchange error: {e}")


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
