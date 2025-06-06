import streamlit as st
import os, io
import boto3
from datetime import datetime
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
        st.success(f"✅ Uploaded `{filename}` to S3 bucket `{AWS_BUCKET}`")
    except Exception as e:
        st.error(f"❌ Upload Failed: {e}")

def media_stream():
    st.subheader("🎥 Record or Upload Media")
    st.info("Record video/audio in-browser or upload manually.")

    mode = st.radio("Choose Input Mode:", ["Record Video", "Record Audio", "Upload File"])

    # -- Load RecordRTC JavaScript
    st.markdown("""
    <script src="https://cdn.webrtc-experiment.com/RecordRTC.js"></script>
    """, unsafe_allow_html=True)

    # -- Recorder UI (via HTML and JS)
    if mode in ["Record Video", "Record Audio"]:
        mime = "video/webm" if mode == "Record Video" else "audio/wav"
        label = "video" if mode == "Record Video" else "audio"
        st.markdown(f"""
            <video id="preview" width="320" height="240" autoplay muted playsinline></video>
            <br/>
            <button onclick="startRecording()">🎬 Start</button>
            <button onclick="stopRecording()">🛑 Stop</button>
            <a id="downloadLink" style="display:none;">⬇️ Download</a>
            <script>
            let recorder, stream;
            async function startRecording() {{
                stream = await navigator.mediaDevices.getUserMedia({{{label}: true}});
                document.getElementById('preview').srcObject = stream;
                recorder = RecordRTC(stream, {{ type: '{label}' }});
                recorder.startRecording();
            }}
            async function stopRecording() {{
                await recorder.stopRecording(async function() {{
                    const blob = recorder.getBlob();
                    const url = URL.createObjectURL(blob);
                    document.getElementById('downloadLink').href = url;
                    document.getElementById('downloadLink').download = "recorded.{mime.split('/')[1]}";
                    document.getElementById('downloadLink').textContent = "⬇️ Download Recording";
                    document.getElementById('downloadLink').style.display = "inline";
                }});
                stream.getTracks().forEach(track => track.stop());
            }}
            </script>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.info("After recording, use the download link below and upload manually below.")

    # -- Upload Zone
    uploaded = st.file_uploader("Upload recording (video/audio)", type=["webm", "mp4", "wav", "m4a"])
    if uploaded:
        filename = f"media/{uploaded.name.split('.')[0]}_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.{uploaded.name.split('.')[-1]}"
        upload_to_s3_bytes(uploaded.getvalue(), filename, uploaded.type)
