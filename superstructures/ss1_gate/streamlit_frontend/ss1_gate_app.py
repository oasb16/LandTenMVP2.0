import streamlit as st
import requests
import base64
import json
from datetime import datetime
import jwt
from urllib.parse import quote, unquote
from superstructures.ss1_gate.shared.dynamodb import save_user_profile

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

# === Run Login
def run_login():
    # Step 2: OAuth code/state injection
    if "oauth_code" not in st.session_state and "oauth_state" not in st.session_state:
        # Show login button that redirects to external launcher
        persona = st.session_state["persona"]
        state_json = json.dumps({"persona": persona})
        encoded_state = quote(state_json)
        st.session_state["oauth_state"] = encoded_state  # Track for later
        st.success(f"Selected state_json: {persona} {state_json} {encoded_state}")   

        # login_url = (
        #     f"https://us-east-1liycxnadt.auth.us-east-1.amazoncognito.com/oauth2/authorize"
        #     f"?identity_provider=Google"
        #     f"&redirect_uri={REDIRECT_URI}"
        #     f"&response_type=CODE"
        #     f"&client_id={CLIENT_ID}"
        #     f"&state={encoded_state}"
        #     f"&scope=email+openid+phone"
        # )

        st.link_button(
            "🔐 Login with GOOOOGLE SSO",
            "http://landten-login-redirect.s3-website-us-east-1.amazonaws.com/login-redirect.html"
        )
        st.stop()

    code = st.session_state.get("oauth_code")
    state_raw = st.session_state.get("oauth_state")

    # Step 3: Decode persona from state
    try:
        decoded_state = json.loads(unquote(state_raw))
        persona = decoded_state.get("persona", "none")
        st.session_state["persona"] = persona
        st.success(f"Decoded persona from state: {persona}")
    except:
        st.error("Failed to decode state param. Defaulting to current persona.")

    # Step 4: Handle token exchange
    if code:
        if st.session_state.get("last_code") == code:
            st.warning("⚠️ Duplicate login attempt. Refresh if stuck.")
            return
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
                        "email": user_info.get("email", ""),
                        "persona": persona,
                        "login_source": "GoogleSSO",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    st.success("User profile written to DB successfully.")
                except Exception as db_error:
                    st.error(f"DB write failed: {db_error}")

                # st.rerun()

            else:
                st.error(f"OAuth token request failed: {res.text}")
        except Exception as e:
            st.error(f"Token exchange error: {e}")
