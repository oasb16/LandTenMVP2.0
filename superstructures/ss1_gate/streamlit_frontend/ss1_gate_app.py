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
                .login-wrapper {
                    display: flex;
                    height: 80vh;
                    justify-content: center;
                    align-items: center;
                    background: linear-gradient(135deg, #f2f8ff, #e0ecf9);
                    font-family: 'Segoe UI', sans-serif;
                }

                .login-box {
                    text-align: center;
                    padding: 40px;
                    border-radius: 12px;
                    background: white;
                    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
                }

                .login-title {
                    font-size: 28px;
                    margin-bottom: 20px;
                    color: #333;
                }

                .role-note {
                    font-size: 16px;
                    margin-bottom: 30px;
                    color: #555;
                }

                .login-button {
                    font-size: 20px;
                    padding: 18px 40px;
                    background-color: #0b72e7;
                    color: white;
                    text-decoration: none;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    transition: background-color 0.3s ease, transform 0.2s ease;
                    display: inline-block;
                }

                .login-button:hover {
                    background-color: #095bb5;
                    transform: translateY(-2px);
                }

            </style>

            <div class="login-wrapper">
                <div class="login-box">
                    <div class="login-title">🔐 Welcome to LandTen 2.0</div>
                    <div class="role-note">
                        Please log in using your Google account to access your dashboard.<br>
                        This portal supports <b>Tenants</b>, <b>Contractors</b>, and <b>Landlords</b>.
                    </div>
                    <a class="login-button" href="http://landten-login-redirect.s3-website-us-east-1.amazonaws.com/login-redirect.html">
                        Login with Google SSO
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
