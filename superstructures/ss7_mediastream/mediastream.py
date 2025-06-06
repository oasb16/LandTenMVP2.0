# mediastream.py
from superstructures.ss7_mediastream.webrtc_debug import media_stream
from superstructures.ss7_mediastream.upload_pipeline import handle_uploaded_media

def run_media_interface(mode="upload"):
    if mode == "upload":
        return handle_uploaded_media()
    elif mode == "capture":
        return media_stream()  # <-- Route capture to new media_stream
    return None
