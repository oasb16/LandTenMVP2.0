import streamlit as st
from streamlit_webrtc import webrtc_streamer
import boto3
import av
import os
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")


def upload_to_s3(file_bytes, filename, content_type):
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        s3.put_object(
            Bucket=AWS_S3_BUCKET_NAME,
            Key=filename,
            Body=file_bytes,
            ContentType=content_type
        )
        st.success(f"✅ Uploaded to S3: `{filename}`")
    except Exception as e:
        st.error(f"❌ S3 Upload Failed: {e}")


def video_frame_callback(frame):
    img = frame.to_image()
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    upload_to_s3(buffer.getvalue(), "captured_image.jpg", "image/jpeg")
    return frame


def audio_frame_callback(frame):
    audio_np = frame.to_ndarray()
    buffer = io.BytesIO(audio_np.tobytes())
    upload_to_s3(buffer.getvalue(), "captured_audio.wav", "audio/wav")
    return frame


def media_stream():
    st.header("Media Stream")
    media_type = st.radio("Choose media type:", ["Video", "Audio"], horizontal=True)

    if media_type == "Video":
        webrtc_streamer(
            key="video_stream",
            video_frame_callback=video_frame_callback,
            media_stream_constraints={"video": True, "audio": False}
        )
    elif media_type == "Audio":
        webrtc_streamer(
            key="audio_stream",
            audio_frame_callback=audio_frame_callback,
            media_stream_constraints={"video": False, "audio": True}
        )
