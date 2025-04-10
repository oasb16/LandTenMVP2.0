import os, json
from datetime import datetime

LOG_DIR = "logs"

def _log_path(thread_id):
    return os.path.join(LOG_DIR, f"chat_thread_{thread_id}.json")

def load_chat_log(thread_id):
    path = _log_path(thread_id)
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def append_chat_log(thread_id, entry):
    path = _log_path(thread_id)
    log = load_chat_log(thread_id)
    log.append(entry)
    with open(path, "w") as f:
        json.dump(log, f, indent=2)
