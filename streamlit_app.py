import streamlit as st
import asyncio
import websockets
import threading
import subprocess
import json

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

from superstructures.ss5_summonengine.summon_engine import get_all_threads_from_dynamodb, delete_all_threads_from_dynamodb, upload_thread_to_s3, save_message_to_dynamodb
from uuid import uuid4
from datetime import datetime
import logging

# Verify secrets configuration
try:
    CLIENT_ID = st.secrets["COGNITO_CLIENT_ID"]
    REDIRECT_URI = "https://landtenmvp20.streamlit.app/"
    COGNITO_DOMAIN = "https://us-east-1liycxnadt.auth.us-east-1.amazoncognito.com"
except KeyError as e:
    st.error(f"Missing required secret: {e.args[0]}")
    st.stop()

# WebSocket server URL
WEBSOCKET_SERVER_URL = "ws://localhost:8765"

# Start the WebSocket server as a separate process
def start_websocket_server():
    subprocess.Popen(["python", "websocket_server.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Start the WebSocket server
start_websocket_server()

# WebSocket client to receive real-time notifications
def start_websocket_client():
    async def listen():
        async with websockets.connect(WEBSOCKET_SERVER_URL) as websocket:
            while True:
                message = await websocket.recv()
                notification = json.loads(message)
                if notification.get("type") == "notification":
                    st.toast(notification.get("message"))  # Display notification using Streamlit's toast

    asyncio.run(listen())

# Start WebSocket client in a separate thread
threading.Thread(target=start_websocket_client, daemon=True).start()

# Function to generate dummy threads
def generate_dummy_threads():
    dummy_threads = []
    for i in range(5):
        thread_id = str(uuid4())
        dummy_data = {
            "thread_id": thread_id,
            "chat_log": [
                {"id": str(uuid4()), "timestamp": datetime.utcnow().isoformat(), "role": "tenant", "message": f"Dummy message {i+1} from tenant.", "thread_id": thread_id, "email": "dummy@example.com"},
                {"id": str(uuid4()), "timestamp": datetime.utcnow().isoformat(), "role": "agent", "message": f"Dummy reply {i+1} from agent.", "thread_id": thread_id, "email": "dummy@example.com"}
            ]
        }
        try:
            save_message_to_dynamodb(thread_id, dummy_data["chat_log"][0])
            save_message_to_dynamodb(thread_id, dummy_data["chat_log"][1])
            upload_thread_to_s3(thread_id, dummy_data["chat_log"])
            dummy_threads.append(thread_id)
        except Exception as e:
            logging.error(f"Error generating dummy thread {thread_id}: {e}")
            st.error(f"Failed to generate thread {thread_id}: {e}")
    return dummy_threads

# Update thread_options to remove redundancy and show the latest content
def fetch_and_display_threads():
    threads = get_all_threads_from_dynamodb()
    logging.debug(f"Fetched threads: {threads}")

    # Use a dictionary to ensure unique thread_ids and keep the latest content
    unique_threads = {}
    for t in threads:
        if 'thread_id' in t:
            unique_threads[t['thread_id']] = t
        else:
            logging.warning(f"Thread missing 'thread_id': {t}")

    # Sort threads by timestamp (latest first) if available
    sorted_threads = sorted(unique_threads.values(), key=lambda x: x.get('timestamp', ''), reverse=True)

    thread_options = ["Select a Thread"] + [t['thread_id'] for t in sorted_threads]
    return thread_options

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

    # Fetch and display threads
    thread_options = fetch_and_display_threads()
    selected_thread = st.selectbox("Select a Thread", options=thread_options)

    if selected_thread != "Select a Thread":
        if st.session_state.get('selected_thread') != selected_thread:
            st.session_state['selected_thread'] = selected_thread
            # Load the chat log for the selected thread
            st.session_state['chat_log'] = [t for t in get_all_threads_from_dynamodb() if t['thread_id'] == selected_thread]

    # Add a button to delete all threads
    if st.button("Delete All Threads"):
        try:
            delete_all_threads_from_dynamodb()
            st.session_state['selected_thread'] = None  # Clear selected thread
            st.success("All threads have been deleted.")
            st.rerun()
        except Exception as e:
            logging.error(f"Error deleting threads: {e}")
            st.error(f"Failed to delete threads: {e}")

    # Add a button to generate 5 dummy threads
    if st.button("Generate Dummy Threads"):
        dummy_threads = generate_dummy_threads()
        st.success(f"Generated 5 dummy threads: {', '.join(dummy_threads)}")
        st.rerun()

# -- Main Layout
persona = st.session_state.get("persona", "tenant")

st.title(f"{persona.capitalize()} Dashboard")

# Display messages for the selected thread
if st.session_state.get('selected_thread'):
    with st.expander("Messages in Current Thread", expanded=False):
        st.subheader(f"Messages in Thread: {st.session_state['selected_thread']}")
        for message in st.session_state['chat_log']:
            # Validate message object and handle missing keys
            role = message.get('role', 'Unknown').capitalize()
            content = message.get('message', '[No content available]')
            if role == 'Agent' and 'Agent error' in content:
                content = '[Agent encountered an error while processing the message.]'
            st.markdown(f"**{role}**: {content}")

        # # Ensure thread content is stored in S3
        # if st.session_state.get('chat_log'):
        #     upload_thread_to_s3(st.session_state['selected_thread'], st.session_state['chat_log'])

# Function to send a message and update the selected thread state
def send_message_and_update_thread(thread_id, message):
    # Send the message to the backend (DynamoDB and S3)
    save_message_to_dynamodb(thread_id, message)
    upload_thread_to_s3(thread_id, st.session_state['chat_log'])

    # Re-fetch the updated thread messages from S3
    updated_thread = [t for t in get_all_threads_from_dynamodb() if t['thread_id'] == thread_id]
    st.session_state['chat_log'] = updated_thread
    st.rerun()  # Trigger UI update


# st.subheader("Chat Window")
# if st.session_state.get('selected_thread'):
#     message = st.text_input("Type your message here...")
#     if st.button("Send"):
#         send_message_and_update_thread(st.session_state['selected_thread'], {
#             "id": str(uuid4()),
#             "timestamp": datetime.utcnow().isoformat(),
#             "role": "tenant",
#             "message": message,
#             "thread_id": st.session_state['selected_thread'],
#             "email": st.session_state.get('email', 'unknown')
#         })
# Call the run_chat_core function to render the chat interface and sidebar controls
run_chat_core()

# Right column: Persona-specific container

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
