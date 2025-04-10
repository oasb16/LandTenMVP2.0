from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import streamlit as st
import numpy as np
import boto3
import io
import os
from dotenv import load_dotenv
load_dotenv()

AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET_NAME")

def upload_to_s3_bytes(byte_data, filename, content_type):
    s3 = boto3.client("s3")
    s3.put_object(Bucket=AWS_S3_BUCKET, Key=filename, Body=byte_data, ContentType=content_type)

def video_frame_callback(frame):
    img = frame.to_image()
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    upload_to_s3_bytes(buffer.read(), "tenant_capture.jpg", "image/jpeg")
    return frame

def audio_frame_callback(frame):
    audio_bytes = frame.to_ndarray().tobytes()
    upload_to_s3_bytes(audio_bytes, "tenant_audio.wav", "audio/wav")
    return frame

def media_stream():
    st.header("Media Stream")

    mode = st.radio("Choose media type", ["Video", "Audio"])

    if mode == "Video":
        st.info("🎥 Recording will auto-capture frames to S3")
        webrtc_streamer(
            key="video",
            mode=WebRtcMode.SENDRECV,
            video_frame_callback=video_frame_callback,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

    elif mode == "Audio":
        st.info("🎤 Recording will auto-capture audio chunks to S3")
        webrtc_streamer(
            key="audio",
            mode=WebRtcMode.SENDRECV,
            audio_frame_callback=audio_frame_callback,
            media_stream_constraints={"video": False, "audio": True},
            async_processing=True,
        )
