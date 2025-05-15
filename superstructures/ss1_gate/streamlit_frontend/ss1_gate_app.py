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
                .landten-login-container {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 90vh;
                    background: #0e1117;
                }

                .landten-login-box {
                    text-align: center;
                    background: rgba(255, 255, 255, 0.02);
                    padding: 3rem;
                    border-radius: 16px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                    backdrop-filter: blur(6px);
                    border: 1px solid rgba(255,255,255,0.05);
                }

                .landten-title {
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: #f1f1f1;
                    margin-bottom: 0.5rem;
                }

                .landten-subtitle {
                    color: #aaaaaa;
                    font-size: 1rem;
                    margin-bottom: 2.5rem;
                }

                .login-button {
                    background: linear-gradient(90deg, #4f46e5, #9333ea);
                    padding: 1rem 2.5rem;
                    border-radius: 50px;
                    font-size: 1.1rem;
                    color: white;
                    text-decoration: none;
                    font-weight: 500;
                    box-shadow: 0 8px 20px rgba(147, 51, 234, 0.3);
                    transition: all 0.3s ease;
                }

                .login-button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 10px 25px rgba(147, 51, 234, 0.4);
                }
            </style>

            <div class="landten-login-container">
                <div class="landten-login-box">
                    <div class="landten-title">LandTen 2.0</div>
                    <div class="landten-subtitle">Unified Login for Landlords, Tenants & Contractors</div>
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
