import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import io
import boto3
import os
from datetime import datetime

# Load AWS credentials from environment
AWS_BUCKET = st.secrets["S3_BUCKET"]
AWS_REGION = st.secrets["AWS_REGION"]  # default fallback

def upload_to_s3_bytes(data: bytes, filename: str, content_type: str):
    try:
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=AWS_BUCKET,
            Key=filename,
            Body=data,
            ContentType=content_type
        )
        st.success(f"✅ Uploaded {filename} to S3.")
    except Exception as e:
        st.error(f"❌ Failed to upload {filename}: {str(e)}")

def video_frame_callback(frame):
    image = frame.to_image()
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    buf.seek(0)
    timestamp = datetime.utcnow().isoformat()
    upload_to_s3_bytes(buf.read(), f"video_frame_{timestamp}.jpg", "image/jpeg")
    return frame

def audio_frame_callback(frame):
    audio_bytes = frame.to_ndarray().tobytes()
    timestamp = datetime.utcnow().isoformat()
    upload_to_s3_bytes(audio_bytes, f"audio_chunk_{timestamp}.wav", "audio/wav")
    return frame

def media_stream():
    st.header("📡 Media Stream (Debug Enabled)")

    # Status check
    if not AWS_BUCKET:
        st.error("❌ AWS_S3_BUCKET_NAME not set in environment variables.")
        return

    st.info(f"🪣 Using S3 Bucket: `{AWS_BUCKET}`")

    media_type = st.radio("Select Media Type:", ["Video", "Audio"], horizontal=True)

    if media_type == "Video":
        st.warning("🎥 Capturing live video frames to S3")
        webrtc_streamer(
            key="video",
            mode=WebRtcMode.SENDRECV,
            video_frame_callback=video_frame_callback,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

    elif media_type == "Audio":
        st.warning("🎤 Capturing live audio chunks to S3")
        webrtc_streamer(
            key="audio",
            mode=WebRtcMode.SENDRECV,
            audio_frame_callback=audio_frame_callback,
            media_stream_constraints={"video": False, "audio": True},
            async_processing=True,
        )
