# tri_chat_core.py (ScarOS hardened)
import streamlit as st, json, os
from datetime import datetime
from uuid import uuid4
from streamlit_elements import elements
import logging
import traceback
import streamlit.components.v1 as components

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

from superstructures.ss5_summonengine.summon_engine import run_summon_engine, save_message_to_dynamodb
from superstructures.ss7_mediastream import run_media_interface
from superstructures.ss8_canvascard.canvascard import create_canvas_card
from utils.chat_log_writer import load_chat_log, append_chat_log

def initialize_session_state():
    if "persona" not in st.session_state:
        st.session_state["persona"] = "tenant"
    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = str(uuid4())
        initial_message = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": "system",
            "message": "New conversation started.",
            "persona": st.session_state.get("persona", "unknown"),
            "user_id": st.session_state.get("email", "unknown"),
            "email": st.session_state.get("email", "unknown"),
            "thread_id": st.session_state["thread_id"]
        }
        try:
            save_message_to_dynamodb(st.session_state["thread_id"], initial_message)
        except Exception as e:
            logging.error(f"Failed to save initial message to DynamoDB: {e}")
            logging.error(traceback.format_exc())
        st.session_state.chat_log = [initial_message]
    if "chat_log" not in st.session_state:
        try:
            st.session_state.chat_log = load_chat_log(st.session_state["thread_id"])
        except Exception as e:
            logging.error(f"Failed to load chat log: {e}")
            logging.error(traceback.format_exc())
            st.session_state.chat_log = []
    if "last_action" not in st.session_state:
        st.session_state.last_action = None
    if "show_upload" not in st.session_state:
        st.session_state.show_upload = False
    if "show_capture" not in st.session_state:
        st.session_state.show_capture = False

def render_chat_log(chat_log):
    st.markdown("### 💬 Conversation")

    chat_html = ""
    for msg in chat_log[-30:]:
        role = msg.get("role", "").capitalize()
        content = msg.get("message", "")
        word_count = len(content.split()) if isinstance(content, str) else 0
        use_canvas = word_count > 100 or any(
            kw in content.lower() for kw in ["summary", "inference", "incident", "description", "transcription"]
        ) if isinstance(content, str) else False

        if use_canvas:
            chat_html += f"""
                <div style='background-color:#2b2b2b; padding:12px; margin:12px 0; border-left:4px solid #00c9a7;
                            border-radius:8px; color:#eee;'>
                    <strong>{role} - Summary:</strong><br>{content}
                </div>
            """
        else:
            chat_html += f"""
                <div style='background-color:#1e1e1e; padding:10px; margin:8px 0;
                            border-radius:10px; color:#eee;'>
                    <strong>{role}:</strong><br>{content}
                </div>
            """

    # Full scrollable div with consistent styling
    scrollable_box = f"""
    <div style='height:500px; overflow-y: auto; background-color: #111; 
                padding: 16px; border-radius: 10px; border: 1px solid #333;
                font-family: "Segoe UI", sans-serif; font-size: 14px;'>
        {chat_html}
    </div>
    """

    components.html(scrollable_box, height=520, scrolling=True)

    components.html("""
    <script>
        const container = window.parent.document.querySelector('iframe').parentNode;
        container.scrollTop = container.scrollHeight;
    </script>
""", height=0)

def run_chat_core():
    st.title("Tenant Chat Interface")
    st.subheader("TriChat – Unified Chat Interface")

    initialize_session_state()

    thread_id = st.session_state["thread_id"]
    chat_log = st.session_state.chat_log
    persona = st.session_state["persona"]

    # st.success(chat_log)

    render_chat_log(chat_log)

    with st.sidebar:
        st.markdown("### 🧭 Media Controls")
        if st.button("📁 Toggle Upload"):
            st.session_state.show_upload = not st.session_state.show_upload
            st.session_state.last_action = "toggle_upload"
            st.rerun()
        if st.button("📷 Toggle Capture"):
            st.session_state.show_capture = not st.session_state.show_capture
            st.session_state.last_action = "toggle_capture"
            st.rerun()
        if st.button("🔄 Close All Panels"):
            st.session_state.show_upload = False
            st.session_state.show_capture = False
            st.session_state.last_action = "close_panels"
            st.rerun()

    if st.session_state.show_upload:
        with st.expander("📎 Upload Media", expanded=True):
            media_msg = run_media_interface(mode="upload")
            if media_msg:
                st.session_state.chat_log.append(media_msg)
                append_chat_log(thread_id, media_msg)
                st.session_state.last_action = "media_upload"
                st.rerun()

    if st.session_state.show_capture:
        with st.expander("📹 Record Media", expanded=True):
            media_msg = run_media_interface(mode="capture")
            if media_msg:
                st.session_state.chat_log.append(media_msg)
                append_chat_log(thread_id, media_msg)
                st.session_state.last_action = "media_capture"
                st.rerun()

    # 🧠 Actual chat form
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Type a message...")
        submitted = st.form_submit_button("Send")

    if submitted and user_input.strip():
        user_msg = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": persona,
            "message": user_input.strip(),
            "thread_id": thread_id,
            "email": st.session_state.get("email", "unknown")
        }
        st.session_state.chat_log.append(user_msg)
        append_chat_log(thread_id, user_msg)
        try:
            save_message_to_dynamodb(thread_id, user_msg)
        except Exception as e:
            logging.error(f"Failed to save user message to DynamoDB: {e}")
            logging.error(traceback.format_exc())
        st.session_state.last_action = "text_input"

        try:
            agent_reply = run_summon_engine(
                chat_log=st.session_state.chat_log,
                user_input=user_input.strip(),
                persona=persona,
                thread_id=thread_id
            )
        except Exception as e:
            logging.error(f"Error in run_summon_engine: {e}")
            logging.error(traceback.format_exc())
            agent_reply = f"[Agent error: {str(e)}]"

        if agent_reply:
            agent_msg = {
                "id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "role": "agent",
                "message": agent_reply
            }
            st.session_state.chat_log.append(agent_msg)
            append_chat_log(thread_id, agent_msg)

        st.rerun()
