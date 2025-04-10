import streamlit as st
from streamlit_elements import elements
import json, os
from datetime import datetime
from uuid import uuid4

from superstructures.ss5_summonengine.summon_engine import run_summon_engine
from superstructures.ss7_mediastream import run_media_interface
from superstructures.ss8_canvascard.canvascard import create_canvas_card

CHAT_LOG_PATH = "logs/chat_thread_main.json"

def run_chat_core():
    st.title("Tenant Chat Interface")
    st.subheader("TriChat – Unified Chat Interface")

    if "persona" not in st.session_state:
        st.session_state["persona"] = "tenant"
    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = str(uuid4())

    persona = st.session_state["persona"]
    thread_id = st.session_state["thread_id"]

    if not os.path.exists("logs"):
        os.makedirs("logs")

    try:
        with open(CHAT_LOG_PATH, "r") as f:
            chat_log = json.load(f)
    except:
        chat_log = []

    st.markdown("---")
    st.markdown("### 💬 Conversation")
    with st.container():
        st.markdown("<div style='height: 400px; overflow-y: auto;'>", unsafe_allow_html=True)
        for msg in chat_log[-30:]:
            role = msg.get("role", "").capitalize()
            content = msg.get("message", "")
            word_count = len(content.split())
            use_canvas = word_count > 100 or any(
                kw in content.lower() for kw in ["summary", "inference", "incident", "description", "transcription"]
            )

            if use_canvas:
                with elements(f"canvas_{msg['id']}"):
                    create_canvas_card(
                        title=f"{role} - Media Summary" if "📎" in content else f"{role} - Long Message",
                        content=content,
                        actions=[]
                    )
            else:
                st.markdown(f"""
                    <div style='background-color:#1e1e1e; padding:10px; margin:8px 0;
                                border-radius:10px; color:#eee;'>
                        <strong>{role}:</strong><br>{content}
                    </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Form + buttons
    col1, col2, col3, col4 = st.columns([5, 1, 1, 1])
    with col1:
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("Type a message...", key="chat_input")
            submitted = st.form_submit_button("Send")
    with col2:
        upload_toggle = st.button("📁 Upload", key="upload_btn")
    with col3:
        capture_toggle = st.button("📷 Capture", key="capture_btn")
    with col4:
        if st.button("🔄 Close All Media Panels"):
            st.session_state.show_upload = False
            st.session_state.show_capture = False

    if "show_upload" not in st.session_state:
        st.session_state.show_upload = False
    if "show_capture" not in st.session_state:
        st.session_state.show_capture = False

    if upload_toggle:
        st.session_state.show_upload = not st.session_state.show_upload
    if capture_toggle:
        st.session_state.show_capture = not st.session_state.show_capture

    if st.session_state.show_upload:
        with st.expander("📎 Upload Media (Audio / Image)", expanded=True):
            run_media_interface(mode="upload")

    if st.session_state.show_capture:
        with st.expander("🎥 Record Live Audio/Video", expanded=True):
            run_media_interface(mode="capture")

    if submitted and user_input.strip():
        user_msg = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": persona,
            "message": user_input.strip()
        }
        chat_log.append(user_msg)

        try:
            agent_reply = run_summon_engine(chat_log, user_input.strip(), persona, thread_id)
        except Exception as e:
            agent_reply = f"[Agent error: {str(e)}]"

        if agent_reply:
            agent_msg = {
                "id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "role": "agent",
                "message": agent_reply
            }
            chat_log.append(agent_msg)

        with open(CHAT_LOG_PATH, "w") as f:
            json.dump(chat_log, f, indent=2)

        st.rerun()
