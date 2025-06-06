import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import boto3
import os
import io
from datetime import datetime
from PIL import Image

# ------------------------
# 🔐 Safe Environment Config
# ------------------------
AWS_BUCKET = st.secrets.get("AWS_S3_BUCKET", "LandTena")
AWS_REGION = st.secrets.get("AWS_REGION", "us-east-1")
S3_PREFIX = "media/"  # Optional: adjust or expose to user

# ------------------------
# ⬆️ Upload Utility
# ------------------------
def upload_to_s3_bytes(byte_data, filename, content_type):
    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.put_object(
            Bucket=AWS_BUCKET,
            Key=filename,
            Body=byte_data,
            ContentType=content_type
        )
        st.success(f"✅ Uploaded: `{filename}`")
    except Exception as e:
        st.error(f"❌ S3 Upload Failed: {e}")

# ------------------------
# 🎥 Video Frame Handler
# ------------------------
def video_frame_callback(frame):
    img = frame.to_image()
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")
    filename = f"{S3_PREFIX}video_snapshot_{ts}.jpg"
    upload_to_s3_bytes(buffer.read(), filename, "image/jpeg")
    return frame

# ------------------------
# 🎤 Audio Frame Handler
# ------------------------
def audio_frame_callback(frame):
    audio_bytes = frame.to_ndarray().tobytes()

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")
    filename = f"{S3_PREFIX}audio_chunk_{ts}.wav"
    upload_to_s3_bytes(audio_bytes, filename, "audio/wav")
    return frame

# ------------------------
# 🚀 Main Stream Interface
# ------------------------
def media_stream():
    st.subheader("🛰️ Live Media Debug Stream")
    st.caption(f"S3 Bucket: `{AWS_BUCKET}`  |  Region: `{AWS_REGION}`")

    media_mode = st.radio("Select Stream Type", ["📷 Video", "🎙️ Audio"])

    if media_mode == "📷 Video":
        snapshot_toggle = st.checkbox("📸 Capture Video Snapshots to S3", value=True)
        st.warning("Camera access required. Allow browser permissions.")

        webrtc_streamer(
            key="video_debug_stream",
            mode=WebRtcMode.SENDRECV,
            video_frame_callback=video_frame_callback if snapshot_toggle else None,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True
        )

    elif media_mode == "🎙️ Audio":
        st.warning("Microphone access required. Allow browser permissions.")

        webrtc_streamer(
            key="audio_debug_stream",
            mode=WebRtcMode.SENDRECV,
            audio_frame_callback=audio_frame_callback,
            media_stream_constraints={"video": False, "audio": True},
            async_processing=True
        )
