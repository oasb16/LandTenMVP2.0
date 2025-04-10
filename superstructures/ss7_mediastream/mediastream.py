import streamlit as st
from streamlit_webrtc import webrtc_streamer
import boto3
import av
import os
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")

def upload_to_s3(file, filename, content_type):
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    s3.put_object(Bucket=AWS_S3_BUCKET_NAME, Key=filename, Body=file, ContentType=content_type)

def video_frame_callback(frame):
    img = frame.to_image()
    # Process the image if needed
    # Convert image to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    # Upload to S3
    upload_to_s3(img_byte_arr, 'captured_image.jpg', 'image/jpeg')
    return frame

def audio_frame_callback(frame):
    audio = frame.to_ndarray()
    # Process the audio if needed
    # Convert audio to bytes
    audio_byte_arr = io.BytesIO(audio.tobytes())
    # Upload to S3
    upload_to_s3(audio_byte_arr, 'captured_audio.wav', 'audio/wav')
    return frame

def media_stream():
    st.header("Media Stream")
    mode = st.radio("Choose media type:", ('Video', 'Audio'))
    if mode == 'Video':
        webrtc_streamer(key="camera", video_frame_callback=video_frame_callback)
    elif mode == 'Audio':
        webrtc_streamer(key="mic", audio_frame_callback=audio_frame_callback)