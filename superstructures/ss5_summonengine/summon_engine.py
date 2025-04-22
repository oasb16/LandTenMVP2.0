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

def get_all_threads_from_dynamodb():
    table = dynamodb.Table(st.secrets["DYNAMODB_TABLE"])
    try:
        response = table.scan()
        return response.get("Items", [])
    except ClientError as e:
        st.error(f"DynamoDB Error: {e.response['Error']['Message']}")
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
