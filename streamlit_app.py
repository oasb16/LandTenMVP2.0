import streamlit as st

st.set_page_config(page_title="LandTen 2.0 – TriChatLite", layout="wide")

from streamlit.components.v1 import html

# -- SS1: Login (Google SSO via Cognito)
from superstructures.ss1_gate.streamlit_frontend.ss1_gate_app import run_login

# -- SS2: Persona router
from superstructures.ss2_pulse.ss2_pulse_app import run_router

# -- SS3: Chat core
from superstructures.ss3_trichatcore.tri_chat_core import run_chat_core

# -- Optional logout logic in sidebar
from urllib.parse import quote

from superstructures.ss5_summonengine.summon_engine import get_all_threads_from_dynamodb, delete_all_threads_from_dynamodb, upload_thread_to_s3, get_thread_from_s3, update_thread_timestamp_in_dynamodb
from uuid import uuid4
from datetime import datetime

# Verify secrets configuration
try:
    CLIENT_ID = st.secrets["COGNITO_CLIENT_ID"]
    REDIRECT_URI = "https://landtenmvp20.streamlit.app/"
    COGNITO_DOMAIN = "https://us-east-1liycxnadt.auth.us-east-1.amazoncognito.com"
except KeyError as e:
    st.error(f"Missing required secret: {e.args[0]}")
    st.stop()

# -- Sidebar
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.get('email', 'Unknown')}**")
    if st.button("Logout"):
        try:
            logout_url = (
                f"{COGNITO_DOMAIN}/logout?"
                f"client_id={CLIENT_ID}&"
                f"logout_uri={REDIRECT_URI}"
            )
            st.session_state.clear()
            st.markdown(f"[🔓 Logged out — click to re-login]({logout_url})")
            st.stop()
        except Exception as e:
            st.error(f"Error during logout: {str(e)}")

    # Fetch all threads
    threads = get_all_threads_from_dynamodb()

    # Display threads in a sidebar
    st.subheader("Available Threads")
    thread_options = ["Select a Thread"] + ["New Thread"] + [t['thread_id'] for t in threads]
    selected_thread = st.selectbox("Select a thread", options=thread_options)

    # Ensure chat_log is initialized in session state
    # Add logging to debug chat_log population
    if selected_thread == "New Thread":
        st.session_state['selected_thread'] = str(uuid4())
        st.session_state['chat_log'] = []  # Initialize chat_log
        st.success("Started a new thread.")
        st.write("Debug: Initialized new thread with empty chat_log.")
        st.rerun()
    elif selected_thread != "Select a Thread":
        st.session_state['selected_thread'] = selected_thread
        st.session_state['chat_log'] = get_thread_from_s3(selected_thread) or []  # Initialize chat_log if not present
        st.write(f"Debug: Loaded chat_log for thread {selected_thread}: {st.session_state['chat_log']}")
        st.rerun()

    # Add a button to delete all threads
    if st.button("Delete All Threads"):
        delete_all_threads_from_dynamodb()
        st.session_state['selected_thread'] = None  # Clear selected thread
        st.success("All threads have been deleted.")
        st.rerun()

# -- Main Layout
persona = st.session_state.get("persona", "tenant")

st.title(f"{persona.capitalize()} Dashboard")

# Main execution flow
if "email" not in st.session_state:
    run_login()
elif "persona" not in st.session_state:
    run_router()

can_run_chat_core = "email" and "persona" in st.session_state
    

# Split layout into two halves
col1, col2 = st.columns([2, 3])

# Left column: Chat window
with col1:
    # Add a scrollable container for the chat window
    if st.session_state.get('selected_thread'):
        st.subheader(f"Messages in Thread: {st.session_state['selected_thread']}")
        thread_messages = st.session_state.get('chat_log', [])
        st.write(f"Debug: Displaying thread_messages: {thread_messages}")  # Log thread messages
        st.markdown(
            """
            <style>
            .scrollable-container {
                height: 400px;
                overflow-y: auto;
                border: 1px solid #ccc;
                padding: 10px;
                background-color: #f9f9f9;
                color: #333;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            .message {
                margin-bottom: 10px;
                padding: 8px;
                border-radius: 5px;
            }
            .user-message {
                background-color: #d1e7dd;
                text-align: left;
            }
            .agent-message {
                background-color: #f8d7da;
                text-align: right;
            }
            </style>
            <div class='scrollable-container'>
            """,
            unsafe_allow_html=True
        )
        for message in thread_messages:
            role_class = "user-message" if message['role'] == "tenant" else "agent-message"
            st.markdown(
                f"<div class='message {role_class}'>"
                f"<strong>{message['role'].capitalize()}:</strong> {message['message']}"
                f"</div>",
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # Real-Time Updates
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("Type a message...")
            submitted = st.form_submit_button("Send")

        if submitted and user_input.strip():
            new_message = {
                "id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "role": st.session_state.get("persona", "user"),
                "message": user_input.strip()
            }
            st.session_state['chat_log'].append(new_message)
            upload_thread_to_s3(st.session_state['selected_thread'], st.session_state['chat_log'])
            update_thread_timestamp_in_dynamodb(st.session_state['selected_thread'])
            st.rerun()
    else: 
        st.error("Please select a thread to view messages.")   

# Right column: Persona-specific container
with col2:
    st.subheader("Details")
    if persona == "tenant":
        st.markdown("### Incidents")
        st.markdown("<div style='height: 200px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;'>Incident details will appear here.</div>", unsafe_allow_html=True)
    elif persona == "landlord":
        st.markdown("### Jobs")
        st.markdown("<div style='height: 200px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;'>Job details will appear here.</div>", unsafe_allow_html=True)
    elif persona == "contractor":
        st.markdown("### Jobs and Schedule")
        st.markdown("<div style='height: 100px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;'>Job details will appear here.</div>", unsafe_allow_html=True)
        st.markdown("<div style='height: 100px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;'>Schedule details will appear here.</div>", unsafe_allow_html=True)
    else:
        st.error("Invalid persona. Please contact support.")

# -- Mobile Compatibility
html("<style>@media (max-width: 768px) { .css-1lcbmhc { flex-direction: column; } }</style>")
