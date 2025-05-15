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
            <style>
                body {
                    background: #f9fbfc;
                    font-family: 'Inter', sans-serif;
                }

                .login-container {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 85vh;
                }

                .login-box {
                    text-align: center;
                }

                .login-title {
                    font-size: 2.2rem;
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                    color: #222;
                }

                .login-sub {
                    font-size: 1rem;
                    color: #666;
                    margin-bottom: 2.5rem;
                }

                .login-button {
                    background-color: #111;
                    color: #fff;
                    padding: 1rem 2.5rem;
                    border-radius: 999px;
                    font-size: 1rem;
                    text-decoration: none;
                    font-weight: 500;
                    transition: background 0.3s ease;
                    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
                }

                .login-button:hover {
                    background-color: #000;
                }
            </style>

            <div class="login-container">
                <div class="login-box">
                    <div class="login-title">LandTen 2.0</div>
                    <div class="login-sub">One login for Landlords, Tenants & Contractors</div>
                    <a class="login-button" href="http://landten-login-redirect.s3-website-us-east-1.amazonaws.com/login-redirect.html">
                        🔐 Login with Google
                    </a>
                </div>
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
