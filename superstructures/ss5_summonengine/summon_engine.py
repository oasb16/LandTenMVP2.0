import streamlit as st
import json
import os
from datetime import datetime
from uuid import uuid4
from utils.gpt_call import call_gpt_agent, call_whisper, call_gpt_vision
from utils.incident_writer import save_incident_from_media
import boto3
from botocore.exceptions import ClientError

MEDIA_PATHS = {
    "audio": "captured_audio.wav",
    "image": "captured_image.jpg"
}

LOG_PATH = "logs/chat_thread_main.json"

# Initialize AWS clients
s3_client = boto3.client('s3',
                         aws_access_key_id=st.secrets["AWS_ACCESS_KEY"],
                         aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
                         region_name=st.secrets["AWS_REGION"])

dynamodb = boto3.resource('dynamodb',
                          aws_access_key_id=st.secrets["AWS_ACCESS_KEY"],
                          aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
                          region_name=st.secrets["AWS_REGION"])

def save_message_to_dynamodb(thread_id, message):
    table = dynamodb.Table(st.secrets["DYNAMODB_TABLE"])
    try:
        table.put_item(Item=message)
    except ClientError as e:
        st.error(f"DynamoDB Error: {e.response['Error']['Message']}")
        print(f"DynamoDB Error: {e.response['Error']['Message']}")
        return False
    return True
def append_chat_log(thread_id, message):    
    table = dynamodb.Table(st.secrets["DYNAMODB_TABLE"])
    try:
        table.update_item(
            Key={'thread_id': thread_id},
            UpdateExpression="SET chat_log = list_append(if_not_exists(chat_log, :empty_list), :message)",
            ExpressionAttributeValues={
                ':message': [message],
                ':empty_list': []
            }
        )
    except ClientError as e:
        st.error(f"DynamoDB Error: {e.response['Error']['Message']}")
        print(f"DynamoDB Error: {e.response['Error']['Message']}")
        return False
    return True
def save_incident_from_media(chat_log, persona, thread_id):
    incident = {
        "id": f"incident_{uuid4()}",
        "full_chat": chat_log,
        "summary": chat_log[-1]["message"],
        "keywords": [],
        "persona": persona,
        "priority": "medium",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Save incident to DynamoDB
    table = dynamodb.Table(st.secrets["DYNAMODB_TABLE"])
    try:
        table.put_item(Item=incident)
    except ClientError as e:
        st.error(f"DynamoDB Error: {e.response['Error']['Message']}")
        print(f"DynamoDB Error: {e.response['Error']['Message']}")
        return False
    return True
def get_chat_log(thread_id):
    table = dynamodb.Table(st.secrets["DYNAMODB_TABLE"])
    try:
        response = table.get_item(Key={'thread_id': thread_id})
        return response.get("Item", {}).get("chat_log", [])
    except ClientError as e:
        st.error(f"DynamoDB Error: {e.response['Error']['Message']}")
        print(f"DynamoDB Error: {e.response['Error']['Message']}")
        return []
def get_thread_id():
    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = str(uuid4())
    return st.session_state["thread_id"]
def get_user_profile():
    if "user_profile" not in st.session_state:
        st.session_state["user_profile"] = {
            "email": st.session_state.get("email", ""),
            "persona": st.session_state.get("persona", "tenant"),
            "login_source": "GoogleSSO",
            "timestamp": datetime.utcnow().isoformat()
        }
    return st.session_state["user_profile"]
def enforce_word_limit(user_input, max_words):
    word_count = len(user_input.split())
    if word_count > max_words:
        st.warning(f"Please limit your message to {max_words} words.")
        return False
    return True
def run_chat_core():
    thread_id = get_thread_id()
    chat_log = get_chat_log(thread_id)
    persona = st.session_state.get("persona", "tenant")

    # Display chat messages
    for message in chat_log:
        if message["role"] == "user":
            st.markdown(f"**{persona.capitalize()}**: {message['message']}")
        else:
            st.markdown(f"**Agent**: {message['message']}")

    # Media upload and capture
    if st.session_state.get("show_upload", False):
        uploaded_file = st.file_uploader("Upload a file", type=["jpg", "png", "wav"])
        if uploaded_file:
            media_url = upload_media_to_s3(uploaded_file, thread_id)
            if media_url:
                media_msg = {
                    "id": str(uuid4()),
                    "timestamp": datetime.utcnow().isoformat(),
                    "role": persona,
                    "message": f"[Media uploaded]({media_url})"
                }
                append_chat_log(thread_id, media_msg)
                st.session_state.last_action = "media_upload"
                st.rerun()

    if st.session_state.get("show_capture", False):
        # Placeholder for media capture logic
        pass
    # Chat form
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Type a message...")
        submitted = st.form_submit_button("Send")
    if submitted and user_input.strip():   
        append_chat_log(thread_id, {"message": combined_reply, "role": "agent"})
        user_msg = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": persona,
            "message": user_input.strip()
        }
        append_chat_log(thread_id, user_msg)
        st.session_state.last_action = "text_input"
        try:
            agent_reply = run_summon_engine(
                chat_log=chat_log,
                user_input=user_input.strip(),
                persona=persona,
                thread_id=thread_id
            )
        except Exception as e:
            st.error(f"Error in run_summon_engine: {e}")
            agent_reply = f"[Agent error: {str(e)}]"
        if agent_reply:
            agent_msg = {
                "id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "role": "agent",
                "message": agent_reply
            }
            append_chat_log(thread_id, agent_msg)
            st.session_state.last_action = "text_input"
            st.session_state.chat_log.append(agent_msg)




def get_all_threads_from_dynamodb():
    table = dynamodb.Table(st.secrets["DYNAMODB_TABLE"])
    try:
        response = table.scan()
        return response.get("Items", [])
    except ClientError as e:
        st.error(f"DynamoDB Error: {e.response['Error']['Message']}")
        print(f"DynamoDB Error: {e.response['Error']['Message']}")
        return []

def upload_media_to_s3(file, thread_id):
    try:
        file_key = f"media/{thread_id}/{file.name}"
        s3_client.upload_fileobj(file, st.secrets["S3_BUCKET"], file_key)
        return f"https://{st.secrets['S3_BUCKET']}.s3.amazonaws.com/{file_key}"
    except ClientError as e:
        st.error(f"S3 Upload Error: {e.response['Error']['Message']}")
        return None

def run_summon_engine(chat_log, user_input, persona, thread_id):
    if not st.session_state.get("agent_active", True):
        return

    st.info("🤖 Agent analyzing...")

    # 1. GPT on user input
    reply = call_gpt_agent(chat_log)

    # 2. Media Checks
    media_summary = ""
    if os.path.exists(MEDIA_PATHS["audio"]):
        try:
            transcription = call_whisper(MEDIA_PATHS["audio"])
            media_summary += f"\n📣 Whisper Transcript: {transcription}"
        except Exception as e:
            media_summary += f"\n[Whisper error: {e}]"

    if os.path.exists(MEDIA_PATHS["image"]):
        try:
            image_desc = call_gpt_vision(MEDIA_PATHS["image"])
            media_summary += f"\n🖼️ Image Summary: {image_desc}"
        except Exception as e:
            media_summary += f"\n[Vision error: {e}]"

    # 3. Append to chat
    combined_reply = reply + media_summary
    agent_msg = {
        "id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "role": "agent",
        "message": combined_reply
    }
    chat_log.append(agent_msg)

    with open(LOG_PATH, "w") as f:
        json.dump(chat_log, f, indent=2)

    # Save message to DynamoDB
    save_message_to_dynamodb(thread_id, agent_msg)

    # 4. Trigger Incident Detection
    try:
        save_incident_from_media(chat_log, persona, thread_id)
    except Exception as e:
        st.warning(f"Incident detection failed: {e}")

    st.success("💡 Agent updated with media context.")
