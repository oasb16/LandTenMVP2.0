import streamlit as st
import boto3
import os
from utils.gpt_call import call_whisper, call_gpt_vision
from utils.incident_writer import save_incident_from_media

from dotenv import load_dotenv
load_dotenv()

AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
AWS_S3_BUCKET = st.secrets["S3_BUCKET"]
s3 = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)


def upload_file(file, filename, content_type):
    try:
        st.success(f"AWS_S3_BUCKET : {AWS_S3_BUCKET}")
        s3.upload_fileobj(file, AWS_S3_BUCKET, filename, ExtraArgs={"ContentType": content_type})
        st.success(f"✅ Uploaded: `{filename}` to bucket `{AWS_S3_BUCKET}`")
        return True
    except Exception as e:
        st.error(f"❌ Upload failed: {str(e)}")
        return False

def handle_uploaded_media():
    st.markdown("### 📤 Upload Recorded Audio/Video/Image")

    uploaded_file = st.file_uploader("Choose a file", type=["jpg", "jpeg", "png", "wav", "mp4"])
    if uploaded_file is not None:
        filename = f"uploads/{uploaded_file.name}"
        content_type = uploaded_file.type

        if upload_file(uploaded_file, filename, content_type):
            if "audio" in content_type:
                with st.spinner("Transcribing audio..."):
                    transcript = call_whisper(uploaded_file)
                    st.success("🧠 Transcription complete:")
                    st.code(transcript)
                    save_incident_from_media(transcript)
            elif "image" in content_type:
                with st.spinner("Analyzing image..."):
                    description = call_gpt_vision(uploaded_file)
                    st.success("🧠 Description complete:")
                    st.code(description)
                    save_incident_from_media(description)
            else:
                st.warning("File uploaded but no analysis triggered (unsupported type).")
