# chat_log_writer.py
import os, json

def get_chat_log_path(thread_id):
    return f"logs/chat_thread_{thread_id}.json"

def load_chat_log(thread_id):
    path = get_chat_log_path(thread_id)
    if not os.path.exists("logs"):
        os.makedirs("logs")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return []

def append_chat_log(thread_id, message):
    path = get_chat_log_path(thread_id)
    log = load_chat_log(thread_id)
    log.append(message)
    with open(path, "w") as f:
        json.dump(log, f, indent=2)
