import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import boto3
import os
import io
from datetime import datetime
import uuid

# Load AWS creds from .env or environment
AWS_BUCKET = st.secrets["S3_BUCKET"]
AWS_REGION = st.secrets["AWS_REGION"]
assert AWS_BUCKET, "❌ Missing AWS_S3_BUCKET_NAME"

# --- S3 uploader ---
def upload_to_s3_bytes(byte_data, filename, content_type):
    try:
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=AWS_BUCKET,
            Key=filename,
            Body=byte_data,
            ContentType=content_type
        )
        st.success(f"✅ Uploaded: {filename}")
    except Exception as e:
        st.error(f"❌ S3 Upload Failed: {str(e)}")

# --- Frame Callbacks ---
def video_frame_callback(frame):
    img = frame.to_image()
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    filename = f"video_frames/frame_{datetime.utcnow().isoformat()}_{uuid.uuid4().hex[:6]}.jpg"
    upload_to_s3_bytes(buffer.read(), filename, "image/jpeg")
    return frame

def audio_frame_callback(frame):
    audio_bytes = frame.to_ndarray().tobytes()
    filename = f"audio_chunks/audio_{datetime.utcnow().isoformat()}_{uuid.uuid4().hex[:6]}.wav"
    upload_to_s3_bytes(audio_bytes, filename, "audio/wav")
    return frame

# --- Main Media UI ---
def media_stream():
    st.markdown("## 🛰️ Media Stream (Debug + Logging Enabled)")

    st.info(f"🪣 S3 Bucket: `{AWS_S3_BUCKET}`")
    media_type = st.radio("Select Media Type", ["Video", "Audio"], horizontal=True)

    st.warning("⚠️ Capturing frames — check logs + S3 for activity")

    if media_type == "Video":
        webrtc_streamer(
            key="video-capture",
            mode=WebRtcMode.SENDRECV,
            video_frame_callback=video_frame_callback,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

    elif media_type == "Audio":
        webrtc_streamer(
            key="audio-capture",
            mode=WebRtcMode.SENDRECV,
            audio_frame_callback=audio_frame_callback,
            media_stream_constraints={"video": False, "audio": True},
            async_processing=True,
        )
