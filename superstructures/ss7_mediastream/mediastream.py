from superstructures.ss7_mediastream.webrtc_debug import media_stream
from superstructures.ss7_mediastream.upload_pipeline import handle_uploaded_media

def run_media_interface(mode="upload"):
    if mode == "upload":
        handle_uploaded_media()
    else:
        media_stream()

    # from utils.chat_log import append_to_chat_log

    # append_to_chat_log({
    #     "id": str(uuid4()),
    #     "timestamp": datetime.utcnow().isoformat(),
    #     "role": "system",
    #     "message": f"📎 Media captured/uploaded and analyzed → Summary: {summary}"
    # })

