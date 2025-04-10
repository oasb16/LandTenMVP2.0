# tri_chat_core.py
import streamlit as st
from streamlit_elements import elements
from datetime import datetime
from uuid import uuid4
from superstructures.ss5_summonengine.summon_engine import run_summon_engine
from superstructures.ss7_mediastream import run_media_interface
from superstructures.ss8_canvascard.canvascard import create_canvas_card
from utils.chat_log_writer import load_chat_log, append_chat_log

def run_chat_core():
    st.title("Tenant Chat Interface")
    st.subheader("TriChat – Unified Chat")

    # 🧠 Init state
    if "persona" not in st.session_state:
        st.session_state["persona"] = "tenant"
    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = str(uuid4())
    if "chat_log" not in st.session_state:
        st.session_state["chat_log"] = load_chat_log(st.session_state["thread_id"])
    if "show_upload" not in st.session_state:
        st.session_state["show_upload"] = False
    if "show_capture" not in st.session_state:
        st.session_state["show_capture"] = False
    if "last_action" not in st.session_state:
        st.session_state["last_action"] = ""

    thread_id = st.session_state["thread_id"]
    persona = st.session_state["persona"]
    chat_log = st.session_state["chat_log"]

    # 💬 Chat window
    st.markdown("### Conversation")
    with st.container():
        st.markdown("<div style='height: 400px; overflow-y: auto;'>", unsafe_allow_html=True)
        for msg in chat_log[-30:]:
            role = msg.get("role", "").capitalize()
            content = msg.get("message", "")
            msg_id = msg.get("id", str(uuid4()))
            if not content:
                continue
            if len(content.split()) > 100 or any(kw in content.lower() for kw in ["summary", "inference", "incident", "description"]):
                with elements(f"canvas_{msg_id}"):
                    create_canvas_card(title=f"{role} – Summary", content=content, actions=[])
            else:
                st.markdown(f"""
                    <div style='background-color:#1e1e1e; padding:10px; margin:8px 0;
                                border-radius:10px; color:#eee;'>
                        <strong>{role}:</strong><br>{content}
                    </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 🎛️ Sidebar controls
    with st.sidebar:
        st.markdown("### Media Controls")
        if st.button("📁 Toggle Upload"):
            st.session_state["show_upload"] = not st.session_state["show_upload"]
        if st.button("📷 Toggle Capture"):
            st.session_state["show_capture"] = not st.session_state["show_capture"]
        if st.button("🔄 Close All Panels"):
            st.session_state["show_upload"] = False
            st.session_state["show_capture"] = False

    # 📎 Media panels
    if st.session_state["show_upload"]:
        with st.expander("📤 Upload Media", expanded=True):
            media_msg = run_media_interface(mode="upload")
            if media_msg:
                append_chat_log(thread_id, media_msg)
                st.session_state["chat_log"].append(media_msg)
                st.session_state["last_action"] = "media_upload"
                st.rerun()

    if st.session_state["show_capture"]:
        with st.expander("🎥 Capture Media", expanded=True):
            media_msg = run_media_interface(mode="capture")
            if media_msg:
                append_chat_log(thread_id, media_msg)
                st.session_state["chat_log"].append(media_msg)
                st.session_state["last_action"] = "media_capture"
                st.rerun()

    # 💬 Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Type your message", key="chat_input")
        submitted = st.form_submit_button("Send")

    if submitted and user_input.strip():
        user_msg = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": persona,
            "message": user_input.strip()
        }
        append_chat_log(thread_id, user_msg)
        st.session_state["chat_log"].append(user_msg)
        st.session_state["last_action"] = "text_input"

        try:
            agent_reply = run_summon_engine(st.session_state["chat_log"], user_input.strip(), persona, thread_id)
        except Exception as e:
            agent_reply = f"[Agent error: {e}]"

        if agent_reply:
            agent_msg = {
                "id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "role": "agent",
                "message": agent_reply
            }
            append_chat_log(thread_id, agent_msg)
            st.session_state["chat_log"].append(agent_msg)

        st.rerun()
