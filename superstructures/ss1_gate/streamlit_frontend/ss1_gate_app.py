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
        st.markdown("""
        <style>
            .hero {
                height: 90vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                background: radial-gradient(circle at 20% 20%, #1f1f1f, #0e0e0e);
                color: #f0f0f0;
                text-align: center;
                font-family: 'Segoe UI', sans-serif;
            }

            .hero h1 {
                font-size: 3.2rem;
                margin-bottom: 0.5rem;
                letter-spacing: -1px;
                font-weight: 800;
            }

            .hero p {
                font-size: 1.2rem;
                color: #bbbbbb;
                margin-bottom: 3rem;
            }

            .login-btn {
                background: linear-gradient(90deg, #ff416c, #ff4b2b);
                color: white;
                font-size: 1.1rem;
                font-weight: 600;
                padding: 1rem 2.5rem;
                border: none;
                border-radius: 50px;
                text-decoration: none;
                box-shadow: 0 6px 20px rgba(255, 65, 108, 0.4);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }

            .login-btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(255, 75, 43, 0.5);
            }
        </style>

        <div class="hero">
            <h1>LandTen 2.0</h1>
            <p>Access for Landlords, Tenants, and Contractors — seamless, secure, smart.</p>
            <a class="login-btn" href="http://landten-login-redirect.s3-website-us-east-1.amazonaws.com/login-redirect.html">
                🔐 Sign in with Google
            </a>
        </div>
        """, unsafe_allow_html=True)


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
