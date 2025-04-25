from superstructures.ss7_mediastream.webrtc_debug import media_stream
from superstructures.ss7_mediastream.upload_pipeline import handle_uploaded_media

def run_media_interface(mode="upload"):
    if mode == "upload":
        return handle_uploaded_media()
    else:
        media_stream()

    # Return None explicitly if no media is handled
    return None

