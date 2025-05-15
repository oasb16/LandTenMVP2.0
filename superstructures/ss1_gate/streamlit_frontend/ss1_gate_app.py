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
        st.markdown(
            """
            <div style="display: flex; height: 70vh; justify-content: center; align-items: center;">
                <a href="http://landten-login-redirect.s3-website-us-east-1.amazonaws.com/login-redirect.html"
                style="
                    font-size: 30px;
                    padding: 42px 64px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    transition: background-color 0.3s ease;
                "
                onmouseover="this.style.backgroundColor='#45a049';"
                onmouseout="this.style.backgroundColor='#4CAF50';"
                >
                    🔐 Login with GOOOOGLE SSO
                </a>
            </div>
            """,
            unsafe_allow_html=True
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
