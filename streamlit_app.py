import streamlit as st
from superstructures.ss1_gate.streamlit_frontend.ss1_gate_app import run_login
from superstructures.ss2_pulse.ss2_pulse_app import run_router

st.set_page_config(page_title="TriChatLite", layout="wide")

if "logged_in" not in st.session_state:
    run_login()       # handles: redirect, token, persona, DB write
else:
    run_router()      # routes to echo, landlord, or contractor based on persona
