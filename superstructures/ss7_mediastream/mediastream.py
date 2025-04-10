import streamlit as st
import os
from datetime import datetime
from uuid import uuid4

UPLOAD_DIR = "logs/uploads"

def media_stream():
    st.markdown("##### 📷 Upload an Image or Video")

    uploaded_file = st.file_uploader("Upload Media", type=["jpg", "png", "jpeg", "mp4", "mov", "avi"])
    
    if uploaded_file is not None:
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        file_ext = uploaded_file.name.split(".")[-1]
        filename = f"{uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"✅ Media saved as: `{filename}`")

        # Display preview
        if file_ext in ["jpg", "png", "jpeg"]:
            st.image(file_path, width=300)
        elif file_ext in ["mp4", "mov", "avi"]:
            st.video(file_path)
