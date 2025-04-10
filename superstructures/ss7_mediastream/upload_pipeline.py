import streamlit as st
import boto3
import os
import json
import base64
from datetime import datetime
from uuid import uuid4
from dotenv import load_dotenv
from utils.gpt_call import call_whisper, call_gpt_vision
from utils.incident_writer import save_incident_from_media

load_dotenv()

AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
AWS_S3_BUCKET = "landtena"

s3 = boto3.client("s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

CHAT_LOG_PATH = "logs/chat_thread_main.json"


def upload_file(file_bytes, filename, content_type):
    try:
        s3.put_object(Bucket=AWS_S3_BUCKET, Key=filename, Body=file_bytes, ContentType=content_type)
        st.success(f"✅ Uploaded `{filename}` to S3 bucket `{AWS_S3_BUCKET}`")
        return True
    except Exception as e:
        st.error(f"❌ Upload failed: {e}")
        return False


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
                st.error("❌ Uploaded file is empty.")
                return

            if not upload_file(file_bytes, filename, content_type):
                return

            result = ""
            file_display = ""

            if "audio" in content_type:
                with st.spinner("🧠 Transcribing with Whisper..."):
                    result = call_whisper(file_bytes)
                    b64_audio = base64.b64encode(file_bytes).decode("utf-8")
                    file_display = f"""
                        <audio controls>
                            <source src="data:{content_type};base64,{b64_audio}" type="{content_type}">
                        </audio>
                    """
                    st.success("🎧 Transcription complete")
                    st.code(result)

            elif "image" in content_type:
                with st.spinner("🧠 Analyzing image with GPT Vision..."):
                    result = call_gpt_vision(file_bytes)
                    b64_img = base64.b64encode(file_bytes).decode("utf-8")
                    file_display = f'<img src="data:{content_type};base64,{b64_img}" width="300"/>'
                    st.success("🖼️ Image description complete")
                    st.code(result)

            else:
                st.warning("⚠️ File uploaded but GPT processing unsupported.")
                return

            # Save incident from inference
            save_incident_from_media(filename, result, content_type)

            # Load and update chat log
            try:
                with open(CHAT_LOG_PATH, "r") as f:
                    chat_log = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                chat_log = []

            chat_log.append({
                "id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "role": "tenant",
                "message": f"""
                    <div style='background:#111;padding:10px;border-radius:10px;'>
                        {file_display}<br><br>
                        <strong>🧠 Agent Inference:</strong><br>{result}
                    </div>
                """
            })

            with open(CHAT_LOG_PATH, "w") as f:
                json.dump(chat_log, f, indent=2)

            st.success("💡 Agent updated with media context.")

        except Exception as e:
            st.error(f"❌ Exception during processing: {e}")
