import streamlit as st
import requests
import base64
import json
from datetime import datetime
import jwt
from urllib.parse import quote, unquote

from superstructures.ss1_gate.persona_extractor import extract_persona
from superstructures.ss1_gate.shared.dynamodb import write_user_profile

# ------------------------------
# Configuration
# ------------------------------
COGNITO_DOMAIN = "https://us-east-1liycxnadt.auth.us-east-1.amazoncognito.com"
REDIRECT_URI = "https://landtenmvpmainapp.streamlit.app/"
CLIENT_ID = st.secrets.get("COGNITO_CLIENT_ID")
CLIENT_SECRET = st.secrets.get("COGNITO_CLIENT_SECRET")
TOKEN_ENDPOINT = f"{COGNITO_DOMAIN}/oauth2/token"

# ------------------------------
# Login Flow
# ------------------------------
def run_login():
    # Step 1: Persona Picker
    if "persona" not in st.session_state:
        st.session_state["persona"] = st.selectbox("Choose your role", ["tenant", "landlord", "contractor"])

    query_params = st.query_params
    code = query_params.get("code", None)
    state_raw = query_params.get("state", None)

    # Step 2: Decode state param (persona)
    try:
        decoded_state = json.loads(unquote(state_raw)) if state_raw else {}
        persona = decoded_state.get("persona", st.session_state.get("persona", "tenant"))
    except:
        persona = st.session_state.get("persona", "tenant")

    # Step 3: Handle OAuth2 code exchange
    if code:
        # Prevent reusing same code
        if st.session_state.get("last_code") == code:
            st.warning("⚠️ Duplicate login attempt — please refresh and retry.")
            return
        st.session_state["last_code"] = code

        # Prepare token request
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
                st.session_state["persona"] = persona

                # DB Sync
                try:
                    write_user_profile({
                        "email": st.session_state["email"],
                        "persona": persona,
                        "login_source": "GoogleSSO",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    st.success(f"✅ Profile saved to DB: {st.session_state['email']} ({persona})")
                except Exception as db_error:
                    st.error(f"❌ DB error: {db_error}")

                # Final cleanup
                st.query_params.clear()
                st.rerun()

            else:
                st.error(f"Login failed: {res.text}")

        except Exception as e:
            st.error(f"Login error: {e}")

    # Step 4: Show login button if not authenticated
    else:
        encoded_state = quote(json.dumps({"persona": st.session_state["persona"]}))
        login_url = (
            f"{COGNITO_DOMAIN}/login?"
            f"client_id={CLIENT_ID}&"
            f"response_type=code&"
            f"scope=email+openid+phone&"
            f"redirect_uri={REDIRECT_URI}&"
            f"state={encoded_state}"
        )
        st.markdown(f"[🔐 Login with Google SSO]({login_url})")
