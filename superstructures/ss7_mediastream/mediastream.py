import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import io
import boto3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # 🔁 Make sure to reload .env

AWS_BUCKET = os.getenv("AWS_S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

def upload_to_s3_bytes(data: bytes, filename: str, content_type: str):
    try:
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=AWS_BUCKET,
            Key=filename,
            Body=data,
            ContentType=content_type
        )
        st.success(f"✅ Uploaded `{filename}` to bucket `{AWS_BUCKET}`.")
        print(f"[DEBUG] Uploaded {filename} to S3.")
    except Exception as e:
        st.error(f"❌ Upload failed: {str(e)}")
        print(f"[ERROR] S3 Upload failed: {str(e)}")

def video_frame_callback(frame):
    try:
        image = frame.to_image()
        buf = io.BytesIO()
        image.save(buf, format="JPEG")
        buf.seek(0)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        filename = f"video_capture_{ts}.jpg"
        upload_to_s3_bytes(buf.read(), filename, "image/jpeg")
        print(f"[DEBUG] Captured frame {filename}")
        return frame
    except Exception as e:
        print(f"[ERROR] Frame conversion failed: {str(e)}")
        return frame

def audio_frame_callback(frame):
    try:
        audio_bytes = frame.to_ndarray().tobytes()
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        filename = f"audio_capture_{ts}.wav"
        upload_to_s3_bytes(audio_bytes, filename, "audio/wav")
        print(f"[DEBUG] Captured audio {filename}")
        return frame
    except Exception as e:
        print(f"[ERROR] Audio frame failed: {str(e)}")
        return frame

def media_stream():
    st.header("📡 Media Stream (Debug + Logging Enabled)")

    if not AWS_BUCKET:
        st.error("❌ S3 Bucket not configured. Check .env or AWS setup.")
        return

    st.success(f"🪣 S3 Bucket: `{AWS_BUCKET}`")
    media_type = st.radio("Select Media Type", ["Video", "Audio"], horizontal=True)

    if media_type == "Video":
        st.warning("🎥 Capturing frames — check logs + S3 for activity")
        webrtc_streamer(
            key="video",
            mode=WebRtcMode.SENDRECV,
            video_frame_callback=video_frame_callback,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

    elif media_type == "Audio":
        st.warning("🎤 Capturing audio chunks — check logs + S3")
        webrtc_streamer(
            key="audio",
            mode=WebRtcMode.SENDRECV,
            audio_frame_callback=audio_frame_callback,
            media_stream_constraints={"video": False, "audio": True},
            async_processing=True,
        )
