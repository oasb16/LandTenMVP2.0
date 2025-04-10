import os, json

LOG_DIR = "logs"

def get_chat_path(thread_id):
    return os.path.join(LOG_DIR, f"chat_thread_{thread_id}.json")

def load_chat_log(thread_id):
    path = get_chat_path(thread_id)
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return []

def append_chat_log(thread_id, msg):
    path = get_chat_path(thread_id)
    log = load_chat_log(thread_id)
    log.append(msg)
    with open(path, "w") as f:
        json.dump(log, f, indent=2)
