import streamlit as st
import boto3
import os
# from superstructures.ss7_mediastream.webrtc_debug import upload_to_s3
from utils.gpt_call import call_whisper, call_gpt_vision
from utils.incident_writer import save_incident_from_media
import json
from datetime import datetime
from uuid import uuid4
from dotenv import load_dotenv
load_dotenv()

AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
# AWS_S3_BUCKET = st.secrets["S3_BUCKET"]
AWS_S3_BUCKET = "landtena"
s3 = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)


def upload_file(file, filename, content_type):
    try:
        st.success(f"AWS_S3_BUCKET : {AWS_S3_BUCKET}")
        s3.upload_fileobj(file, AWS_S3_BUCKET, filename, ExtraArgs={"ContentType": content_type})
        st.success(f"✅ Uploaded: `{filename}` to bucket `{AWS_S3_BUCKET}`")
        return True
    except Exception as e:
        st.error(f"❌ Upload failed: {str(e)}")
        return False


CHAT_LOG_PATH = "logs/chat_thread_main.json"

def handle_uploaded_media():
    st.markdown("### 📤 Upload Recorded Audio/Video/Image")

    uploaded_file = st.file_uploader(
        "Choose a file", type=["jpg", "jpeg", "png", "wav", "mp3", "mp4"]
    )

    if uploaded_file is not None:
        try:
            content_type = uploaded_file.type
            file_bytes = uploaded_file.getvalue()
            filename = f"uploads/{datetime.utcnow().isoformat()}_{uploaded_file.name}"

            if not file_bytes:
                st.error("❌ File appears empty.")
                return

            # # Upload to S3
            # upload_to_s3(file_bytes, filename, content_type)
            # st.success(f"✅ Uploaded to S3 as `{filename}`")

            result = ""

            if "audio" in content_type:
                with st.spinner("Transcribing audio..."):
                    result = call_whisper(file_bytes)
                    st.success("🧠 Transcription complete:")
                    st.code(result)

            elif "image" in content_type:
                with st.spinner("Analyzing image..."):
                    result = call_gpt_vision(file_bytes)
                    st.success("🧠 Image description complete:")
                    st.code(result)

            else:
                st.warning("⚠️ Unsupported file type for GPT processing.")
                return

            # Save to incident DB
            save_incident_from_media(filename, result, content_type)

            # Append to chat log
            chat_msg = {
                "id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "role": "tenant",
                "message": f"[📎 Uploaded: {uploaded_file.name}]\n\n{result}"
            }

            try:
                with open(CHAT_LOG_PATH, "r") as f:
                    chat_log = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                chat_log = []

            chat_log.append(chat_msg)

            with open(CHAT_LOG_PATH, "w") as f:
                json.dump(chat_log, f, indent=2)

            st.success("💡 Agent updated with media context.")

        except Exception as e:
            st.error(f"❌ Upload failed: {e}")

