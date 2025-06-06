import streamlit as st
import boto3
import os
import io
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- AWS CONFIG ---
AWS_BUCKET = os.getenv("AWS_S3_BUCKET_NAME", "LandTena")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# --- Upload Logic ---
def upload_to_s3_bytes(byte_data, filename, content_type):
    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.put_object(
            Bucket=AWS_BUCKET,
            Key=filename,
            Body=byte_data,
            ContentType=content_type
        )
        st.success(f"✅ Uploaded: `{filename}` to bucket: `{AWS_BUCKET}`")
    except Exception as e:
        st.error(f"❌ Upload failed: {e}")

# --- Unified Media Capture Interface ---
def media_stream():
    st.subheader("📡 Media Upload Interface")
    st.info(f"Target Bucket: `{AWS_BUCKET}`")

    mode = st.radio("Select Media Type", ["Take Photo", "Record Audio", "Upload Video"])

    if mode == "Take Photo":
        image = st.camera_input("📸 Capture a photo")
        if image:
            img_bytes = image.getvalue()
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")
            filename = f"media/photo_{timestamp}.jpg"
            upload_to_s3_bytes(img_bytes, filename, "image/jpeg")

    elif mode == "Record Audio":
        audio = st.audio_input("🎤 Record your voice")
        if audio:
            audio_bytes = audio.getvalue()
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")
            filename = f"media/audio_{timestamp}.wav"
            upload_to_s3_bytes(audio_bytes, filename, "audio/wav")

    elif mode == "Upload Video":
        video = st.file_uploader("🎞️ Upload a video file", type=["mp4", "mov", "avi"])
        if video:
            st.video(video)
            video_bytes = video.getvalue()
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")
            filename = f"media/video_{timestamp}.mp4"
            upload_to_s3_bytes(video_bytes, filename, "video/mp4")
