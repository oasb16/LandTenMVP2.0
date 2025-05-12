# upload_pipeline.py
import streamlit as st, boto3, os, json, base64
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

def upload_file(file_bytes, filename, content_type):
    try:
        s3.put_object(Bucket=AWS_S3_BUCKET, Key=filename, Body=file_bytes, ContentType=content_type)
        return True
    except Exception as e:
        st.error(f"Upload error: {e}")
        return False

def handle_uploaded_media():
    uploaded_file = st.file_uploader("Choose a file", type=["jpg", "jpeg", "png", "wav", "mp3", "mp4"])
    if uploaded_file is None:
        return None

    content_type = uploaded_file.type
    file_bytes = uploaded_file.getvalue()
    filename = f"uploads/{datetime.utcnow().isoformat()}_{uploaded_file.name}"
    s3_url = f"https://{AWS_S3_BUCKET}.s3.amazonaws.com/{filename}"

    if not upload_file(file_bytes, filename, content_type):
        return None

    result, file_display = "", ""
    try:
        if "audio" in content_type:
            with st.spinner("Transcribing..."):
                result = call_whisper(file_bytes)
                file_display = f"<audio controls><source src='{s3_url}' type='{content_type}'></audio>"

        elif "image" in content_type:
            with st.spinner("Analyzing image..."):
                result = call_gpt_vision(file_bytes)
                file_display = f"<img src='{s3_url}' width='300'/>"

        save_incident_from_media(filename, result, content_type)

        return {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": "tenant",
            "message": f"""
                <div style='background:#111;padding:10px;border-radius:10px;'>
                    <strong>📎 Media Uploaded:</strong> <a href="{s3_url}" target="_blank">{uploaded_file.name}</a><br>
                    {file_display}<br><br>
                    <strong>🧠 Inference:</strong><br>{result}
                </div>
            """
        }

    except Exception as e:
        st.error(f"Inference failed: {e}")
        return None
