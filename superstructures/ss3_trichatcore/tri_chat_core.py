import streamlit as st
import json, os, logging, traceback, boto3
from datetime import datetime
from uuid import uuid4
from botocore.exceptions import ClientError
import streamlit.components.v1 as components

from superstructures.ss5_summonengine.summon_engine import (
    run_summon_engine, save_message_to_dynamodb, upload_thread_to_s3, get_all_threads_from_dynamodb
)
from superstructures.ss7_mediastream import run_media_interface
from utils.chat_log_writer import append_chat_log

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

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
            "persona": st.session_state["persona"],
            "user_id": st.session_state.get("email", "unknown"),
            "email": st.session_state.get("email", "unknown"),
            "thread_id": st.session_state["thread_id"]
        }
        try:
            save_message_to_dynamodb(st.session_state["thread_id"], initial_message)
        except Exception as e:
            logging.error(f"Failed to save init message: {e}")
            logging.error(traceback.format_exc())
        st.session_state.chat_log = [initial_message]
    if "chat_log" not in st.session_state:
        try:
            thread_id = st.session_state.get("selected_thread", st.session_state["thread_id"])
            all_msgs = [t for t in get_all_threads_from_dynamodb() if t["thread_id"] == thread_id]
            sorted_msgs = sorted(all_msgs, key=lambda x: x["timestamp"])
            st.session_state.chat_log = list({t["id"]: t for t in sorted_msgs}.values())
        except Exception as e:
            logging.error(f"Failed to load chat log: {e}")
            st.session_state.chat_log = []
    if "last_action" not in st.session_state:
        st.session_state.last_action = None
    if "show_upload" not in st.session_state:
        st.session_state.show_upload = False
    if "show_capture" not in st.session_state:
        st.session_state.show_capture = False
    if "thread_media" not in st.session_state:
        st.session_state["thread_media"] = {}
    if "current_thread" not in st.session_state:
        st.session_state["current_thread"] = st.session_state["thread_id"]

def render_chat_log(chat_log):
    messages = {msg["id"]: msg for msg in sorted(chat_log, key=lambda x: x["timestamp"])}.values()
    st.markdown(f"### 💬 Conversation `{st.session_state['current_thread']}`")

    html = ""
    for msg in messages:
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("message", "")
        word_count = len(content.split()) if isinstance(content, str) else 0
        use_canvas = word_count > 100 or any(kw in content.lower() for kw in ["summary", "incident", "description"])

        if use_canvas:
            html += f"""<div style='background:#2b2b2b;padding:12px;margin:12px 0;
                        border-left:4px solid #00c9a7;border-radius:8px;color:#eee'>
                        <strong>{role} - Summary:</strong><br>{content}</div>"""
        else:
            html += f"""<div style='background:#1e1e1e;padding:10px;margin:8px 0;
                        border-radius:10px;color:#eee'><strong>{role}:</strong><br>{content}</div>"""

    box = f"""<div style='height:500px;overflow-y:auto;background:#111;padding:16px;
            border-radius:10px;border:1px solid #333;font-family:"Segoe UI";
            font-size:14px;'>{html}</div>"""
    components.html(box, height=520, scrolling=True)

@st.fragment
def media_control_fragment():
    st.markdown("### 🧭 Media Controls")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📁 Toggle Upload"):
            st.session_state.show_upload = not st.session_state.show_upload
    with col2:
        if st.button("📷 Toggle Capture"):
            st.session_state.show_capture = not st.session_state.show_capture
    with col3:
        if st.button("🔄 Close Panels"):
            st.session_state.show_upload = False
            st.session_state.show_capture = False

    thread_id = st.session_state["current_thread"]

    if st.session_state.show_upload:
        with st.expander("📎 Upload Media", expanded=True):
            msg = run_media_interface("upload")
            if msg:
                st.session_state.chat_log.append(msg)
                append_chat_log(thread_id, msg)
                upload_thread_to_s3(thread_id, st.session_state.chat_log)
                st.session_state.show_upload = False

    if st.session_state.show_capture:
        with st.expander("📹 Record Media", expanded=True):
            msg = run_media_interface("capture")
            if msg:
                st.session_state.chat_log.append(msg)
                append_chat_log(thread_id, msg)
                upload_thread_to_s3(thread_id, st.session_state.chat_log)
                st.session_state.show_capture = False

@st.fragment
def chat_input_fragment():
    st.markdown("💬 To chat with Agent, say @agent")
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Type your message...")
        submitted = st.form_submit_button("Send")

    thread_id = st.session_state["current_thread"]
    persona = st.session_state["persona"]
    user_email = st.session_state.get("email", "unknown")

    if submitted and user_input.strip():
        role = st.session_state.get("user_profile", {}).get("email", persona)
        msg = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": role,
            "message": user_input.strip(),
            "thread_id": thread_id,
            "email": user_email
        }
        st.session_state.chat_log.append(msg)
        append_chat_log(thread_id, msg)
        save_message_to_dynamodb(thread_id, msg)

        try:
            agent_reply = run_summon_engine(
                chat_log=st.session_state.chat_log,
                user_input=user_input.strip(),
                persona=persona,
                thread_id=thread_id
            )
        except Exception as e:
            logging.error(f"Agent error: {e}")
            agent_reply = "[Agent failed to reply.]"

        if agent_reply:
            agent_msg = {
                "id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "role": "agent",
                "message": agent_reply,
                "thread_id": thread_id,
                "email": user_email
            }
            st.session_state.chat_log.append(agent_msg)
            append_chat_log(thread_id, agent_msg)

def prune_empty_threads():
    dynamodb = boto3.resource('dynamodb',
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
        region_name=st.secrets["AWS_REGION"])
    table = dynamodb.Table(st.secrets["DYNAMODB_TABLE"])
    try:
        response = table.scan()
        with table.batch_writer() as batch:
            for item in response.get("Items", []):
                if item.get("message") == "New conversation started.":
                    batch.delete_item(Key={"email": item["email"], "id": item["id"]})
        st.success("🧹 Cleaned empty threads")
    except ClientError as e:
        st.error(f"DynamoDB prune error: {e.response['Error']['Message']}")

def run_chat_core():
    initialize_session_state()

    if st.button("📅 Inject Proposal"):
        proposal = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": "agent",
            "message": "Would you like to schedule a meeting? Slots: [10:00 AM, 2:00 PM, 4:00 PM]",
            "thread_id": st.session_state["current_thread"],
            "email": st.session_state.get("email", "unknown")
        }
        st.session_state.chat_log.append(proposal)
        append_chat_log(st.session_state["current_thread"], proposal)
        upload_thread_to_s3(st.session_state["current_thread"], st.session_state.chat_log)

    render_chat_log(st.session_state.chat_log)
    chat_input_fragment()
    media_control_fragment()
    prune_empty_threads()
