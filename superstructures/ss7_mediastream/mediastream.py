from superstructures.ss7_mediastream.webrtc_debug import media_stream
from superstructures.ss7_mediastream.upload_pipeline import handle_uploaded_media

def run_media_interface():
    import streamlit as st
    st.markdown("## 🖼️ Upload or Capture Media")

    choice = st.radio("Select Media Mode", ["🎥 Live Stream (Debug)", "📤 Upload File (Recommended)"])
    
    if choice == "🎥 Live Stream (Debug)":
        media_stream()
    else:
        handle_uploaded_media()
        chat_log.append({
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "role": "system",
            "message": f"📎 Uploaded file: `{filename}` → summary: {summary_text}"
        })

