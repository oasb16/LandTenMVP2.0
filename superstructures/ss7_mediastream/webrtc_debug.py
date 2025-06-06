import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import boto3
import os
import io
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

AWS_BUCKET = os.getenv("AWS_S3_BUCKET_NAME", "LandTena")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

def upload_to_s3_bytes(byte_data, filename, content_type):
    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.put_object(
            Bucket=AWS_BUCKET,
            Key=filename,
            Body=byte_data,
            ContentType=content_type
        )
        st.success(f"✅ Uploaded: `{filename}` to S3 bucket: `{AWS_BUCKET}`")
    except Exception as e:
        st.error(f"❌ Upload Failed: {e}")

def video_frame_callback(frame):
    img = frame.to_image()
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")
    filename = f"media/video_snapshot_{timestamp}.jpg"
    upload_to_s3_bytes(buffer.read(), filename, "image/jpeg")
    return frame

def audio_frame_callback(frame):
    audio_bytes = frame.to_ndarray().tobytes()
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")
    filename = f"media/audio_chunk_{timestamp}.wav"
    upload_to_s3_bytes(audio_bytes, filename, "audio/wav")
    return frame

def media_stream():
    st.subheader("🛰️ Media Stream (Debug + Logging Enabled)")
    st.info(f"🪣 S3 Bucket: `{AWS_BUCKET}`")

    mode = st.radio("Select Media Type", ["Video", "Audio"])

    if mode == "Video":
        st.warning("📸 Capturing frames — check logs + S3 for activity")
        webrtc_streamer(
            key="video_stream",
            mode=WebRtcMode.SENDRECV,
            video_frame_callback=video_frame_callback,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )
    elif mode == "Audio":
        st.warning("🎤 Capturing audio — check logs + S3 for activity")
        webrtc_streamer(
            key="audio_stream",
            mode=WebRtcMode.SENDRECV,
            audio_frame_callback=audio_frame_callback,
            media_stream_constraints={"video": False, "audio": True},
            async_processing=True,
        )
