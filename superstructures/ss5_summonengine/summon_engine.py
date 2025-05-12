import streamlit as st
import json
import os
from datetime import datetime
from uuid import uuid4
from utils.gpt_call import call_gpt_agent, call_whisper, call_gpt_vision
from utils.incident_writer import save_incident_from_media
import boto3
from botocore.exceptions import ClientError
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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

def validate_message_schema(message):
    required_fields = ["id", "timestamp", "role", "message", "thread_id", "email"]
    missing_fields = [field for field in required_fields if field not in message]
    if missing_fields:
        raise ValueError(f"Message is missing required fields: {missing_fields}")

def save_message_to_dynamodb(thread_id, message):
    try:
        validate_message_schema(message)
        table = dynamodb.Table(st.secrets["DYNAMODB_TABLE"])
        logging.debug(f"Saving message to DynamoDB for thread_id: {thread_id}, message: {message}")
        table.put_item(Item=message)
    except ValueError as ve:
        logging.error(f"Schema validation error: {ve} message to DynamoDB for thread_id: {thread_id}, message: {message}")
        st.error(f"Schema validation error: {ve} message to DynamoDB for thread_id: {thread_id}, message: {message}")
        return False
    except ClientError as e:
        logging.error(f"DynamoDB Error in save_message_to_dynamodb: {e.response['Error']['Message']}")
        st.error(f"DynamoDB Error in save_message_to_dynamodb: {e.response['Error']['Message']}")
        return False
    return True

def append_chat_log(thread_id, message):
    table = dynamodb.Table(st.secrets["DYNAMODB_TABLE"])
    try:
        # If the message contains media, store only the media_key
        if "media" in message:
            media_key = message.pop("media")
            message["media_key"] = media_key

        logging.debug(f"Appending message to chat_log for thread_id: {thread_id}, message: {message}")
        try:
            table.update_item(
                Key={'thread_id': thread_id},
                UpdateExpression="SET chat_log = list_append(if_not_exists(chat_log, :empty_list), :message)",
                ExpressionAttributeValues={
                    ':message': [message],
                    ':empty_list': []
                }
            )
            st.success(f"Chat log updated for thread_id: {thread_id}")
        except ClientError as e:
            logging.error(f"Error appending to chat_log: {e.response['Error']['Message']}")
            st.error(f"Error appending to chat_log: {e.response['Error']['Message']}")
    except ClientError as e:
        logging.error(f"DynamoDB Error in append_chat_log: {e.response['Error']['Message']}")
        st.error(f"DynamoDB Error in append_chat_log: {e.response['Error']['Message']}")
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
        "timestamp": datetime.utcnow().isoformat(),
        "thread_id": thread_id,  # Ensure thread_id is included
        "email": st.session_state.get("email", "unknown")  # Ensure email is included
    }

    # Save incident to DynamoDB
    table = dynamodb.Table(st.secrets["DYNAMODB_TABLE"])
    try:
        table.put_item(Item=incident)
    except ClientError as e:
        st.error(f"DynamoDB Error in save_incident_from_media: {e.response['Error']['Message']}")
        print(f"DynamoDB Error: {e.response['Error']['Message']}")
        return False
    return True

def get_chat_log(thread_id):
    table = dynamodb.Table(st.secrets["DYNAMODB_TABLE"])
    try:
        response = table.get_item(Key={'thread_id': thread_id})
        chat_log = response.get("Item", {}).get("chat_log", [])
        for message in chat_log:
            if "media_key" in message:  # Check if media_key exists
                message["media"] = s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": st.secrets["S3_BUCKET"], "Key": message["media_key"]},
                    ExpiresIn=3600  # URL valid for 1 hour
                )
        return chat_log
    except ClientError as e:
        st.error(f"DynamoDB Error in get_chat_log: {e.response['Error']['Message']}")
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
                st.success(f"Engaged upload_thread_to_s3 from run_chat_core: if st.session_state.get(show_upload, False): {media_msg}")
                upload_thread_to_s3(thread_id, get_chat_log(thread_id))
                st.session_state.last_action = "media_upload"

    if st.session_state.get("show_capture", False):
        # Placeholder for media capture logic
        pass
    # Chat form
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Type a message...")
        submitted = st.form_submit_button("Send")
    if submitted and user_input.strip():   
        append_chat_log(thread_id, {"message": user_input, "role": "agent"})
        user_msg = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": persona,
            "message": user_input.strip()
        }
        st.success(f"Engaged upload_thread_to_s3 from run_chat_core: if submitted and user_input.strip(): {media_msg}")
        append_chat_log(thread_id, user_msg)
        upload_thread_to_s3(thread_id, get_chat_log(thread_id))
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
            st.success(f"Engaged upload_thread_to_s3 from run_chat_core: if agent_reply: {media_msg}")
            append_chat_log(thread_id, agent_msg)
            upload_thread_to_s3(thread_id, get_chat_log(thread_id))
            st.session_state.last_action = "text_input"
            st.session_state.chat_log.append(agent_msg)

def get_all_threads_from_dynamodb():
    table = dynamodb.Table(st.secrets["DYNAMODB_TABLE"])
    try:
        logging.debug("Fetching all threads from DynamoDB")
        response = table.scan()
        logging.debug(f"Fetched threads: {response.get('Items', [])}")
        return response.get("Items", [])
    except ClientError as e:
        logging.error(f"DynamoDB Error in get_all_threads_from_dynamodb: {e.response['Error']['Message']}")
        st.error(f"DynamoDB Error in get_all_threads_from_dynamodb: {e.response['Error']['Message']}")
        return []

def delete_all_threads_from_dynamodb():
    table = dynamodb.Table(st.secrets["DYNAMODB_TABLE"])
    try:
        response = table.scan()
        with table.batch_writer() as batch:
            for item in response.get("Items", []):
                # Use both Partition Key (email) and Sort Key (id) for deletion
                batch.delete_item(Key={
                    "email": item["email"],
                    "id": item["id"]
                })
    except ClientError as e:
        st.error(f"DynamoDB Error in delete_all_threads_from_dynamodb: {e.response['Error']['Message']}")


def upload_thread_to_s3(thread_id, chat_log):
    try:
        file_key = f"threads/{thread_id}.json"

        # Upload the object
        s3_client.put_object(
            Bucket=st.secrets["S3_BUCKET"],
            Key=file_key,
            Body=json.dumps(chat_log, indent=2),
            ContentType="application/json"
        )

        # Generate a pre-signed URL valid for 5 minutes (300 seconds)
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": st.secrets["S3_BUCKET"], "Key": file_key},
            ExpiresIn=300,
            HttpMethod="GET"
        )

        st.success(f"Thread uploaded to S3. To view click [here]({presigned_url})")
        return presigned_url

    except ClientError as e:
        logging.error(f"S3 Upload Error: {e.response['Error']['Message']}")
        st.error(f"S3 Upload Error: {e.response['Error']['Message']}")
        return None


def upload_media_to_s3(file, thread_id):
    try:
        file_key = f"media/{thread_id}/{file.name}"
        logging.debug(f"Uploading media to S3 for thread_id: {thread_id}, file_key: {file_key}")
        s3_client.upload_fileobj(file, st.secrets["S3_BUCKET"], file_key)

        # Generate a presigned URL for the uploaded media
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": st.secrets["S3_BUCKET"], "Key": file_key},
            ExpiresIn=3600  # URL valid for 1 hour
        )

        logging.debug(f"Media uploaded to S3 at URL: {presigned_url}")

        # Create a user message with the presigned URL
        user_msg = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": st.session_state.get("persona", "unknown"),
            "media": presigned_url,
            "thread_id": thread_id,
            "email": st.session_state.get("email", "unknown")
        }

        # Append the message to the chat log and upload the thread to S3
        st.success(f"This is from upload_media_to_s3: {user_msg}")
        append_chat_log(thread_id, user_msg)
        upload_thread_to_s3(thread_id, get_chat_log(thread_id))

        # Display success message with the presigned URL
        st.success(f"Media uploaded successfully! Access it [here]({presigned_url})")

        return presigned_url

    except ClientError as e:
        logging.error(f"S3 Upload Error: {e.response['Error']['Message']}")
        st.error(f"S3 Upload Error: {e.response['Error']['Message']}")
        return None


def get_thread_from_s3(thread_id):
    try:
        logging.debug(f"Fetching thread from S3 for thread_id: {thread_id}")
        file_key = f"threads/{thread_id}.json"
        response = s3_client.get_object(Bucket=st.secrets["S3_BUCKET"], Key=file_key)
        thread_data = json.loads(response['Body'].read().decode('utf-8'))
        logging.debug(f"Fetched thread data: {thread_data}")
        return thread_data
    except ClientError as e:
        logging.error(f"S3 Fetch Error: {e.response['Error']['Message']}")
        st.error(f"S3 Fetch Error: {e.response['Error']['Message']}")
        return []

def run_summon_engine(chat_log, user_input, persona, thread_id):
    if not st.session_state.get("agent_active", True):
        return

    # Check if @agent is mentioned in the user input
    engage_agent = "@agent" in user_input

    if engage_agent:
        st.info("🤖 Agent engaged")

    # Validate chat_log to ensure all messages have the 'role' key
    for message in chat_log:
        message.setdefault("role", "Unknown")
        message.setdefault("message", "[No content available]")

    # 1. GPT on user input (only if @agent is mentioned)
    reply = ""
    if engage_agent:
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
    if engage_agent:
        agent_msg = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": "agent",  # Ensure role is set
            "message": combined_reply,
            "thread_id": thread_id,
            "email": st.session_state.get("email", "unknown")
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

        # 5. Upload thread to S3
        st.success(f"Engaged upload_thread_to_s3 from run_summon_engine:  if engage_agent: {chat_log}")
        upload_thread_to_s3(thread_id, chat_log)

        st.success("💡 Agent updated with media context.")
    else:
        # Save user reply to S3 when agent is not engaged
        user_msg = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": persona,
            "message": user_input.strip(),
            "thread_id": thread_id,
            "email": st.session_state.get("email", "unknown")
        }
        chat_log.append(user_msg)

        with open(LOG_PATH, "w") as f:
            json.dump(chat_log, f, indent=2)

        # Save message to DynamoDB
        save_message_to_dynamodb(thread_id, user_msg)

        # Upload thread to S3
        st.success(f"Engaged upload_thread_to_s3 from run_summon_engine: else engage_agent: {chat_log}")
        upload_thread_to_s3(thread_id, chat_log)

def update_thread_timestamp_in_dynamodb(thread_id):
    table = dynamodb.Table(st.secrets["DYNAMODB_TABLE"])
    try:
        table.update_item(
            Key={"thread_id": thread_id},
            UpdateExpression="SET last_updated = :timestamp",
            ExpressionAttributeValues={":timestamp": datetime.utcnow().isoformat()}
        )
    except ClientError as e:
        st.error(f"DynamoDB Error in update_thread_timestamp_in_dynamodb: {e.response['Error']['Message']}")
