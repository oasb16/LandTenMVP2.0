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
    st.success(f"st.session_state: {st.session_state}")
    if "oauth_code" not in st.session_state and "oauth_state" not in st.session_state:
        # Show login button that redirects to external launcher
        # persona = st.session_state["persona"]
        # state_json = json.dumps({"persona": persona})
        # encoded_state = quote(state_json)
        # st.session_state["oauth_state"] = encoded_state  # Track for later
        # st.success(f"Selected state_json: {persona} {state_json} {encoded_state}")   

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
