import logging
from datetime import datetime
from uuid import uuid4
from superstructures.ss5_summonengine.summon_engine import (
    get_all_threads_from_dynamodb,
    delete_all_threads_from_dynamodb,
    save_message_to_dynamodb,
    upload_thread_to_s3
)

def generate_dummy_threads():
    """Generate dummy threads for testing purposes."""
    dummy_threads = []
    for i in range(5):
        thread_id = str(uuid4())
        dummy_data = {
            "thread_id": thread_id,
            "chat_log": [
                {
                    "id": str(uuid4()), "timestamp": datetime.utcnow().isoformat(),
                    "role": "landlord", "message": f"Landlord note {i+1}", "thread_id": thread_id, "email": "dummy@example.com"
                },
                {
                    "id": str(uuid4()), "timestamp": datetime.utcnow().isoformat(),
                    "role": "agent", "message": f"Agent processed item {i+1}", "thread_id": thread_id, "email": "dummy@example.com"
                }
            ]
        }
        try:
            for msg in dummy_data["chat_log"]:
                save_message_to_dynamodb(thread_id, msg)
            upload_thread_to_s3(thread_id, dummy_data["chat_log"])
            dummy_threads.append(thread_id)
        except Exception as e:
            logging.error(f"[Thread Error] {thread_id}: {e}")
    return dummy_threads

def fetch_and_display_threads():
    """Fetch and display threads from the database."""
    threads = get_all_threads_from_dynamodb()
    unique = {t['thread_id']: t for t in threads if 'thread_id' in t}
    sorted_threads = sorted(unique.values(), key=lambda x: x.get('timestamp', ''), reverse=True)
    return ["Select a Thread"] + [t['thread_id'] for t in sorted_threads]

def delete_all_threads():
    """Delete all threads from the database."""
    delete_all_threads_from_dynamodb()

def prune_empty_threads():
    """Prune threads that only contain default messages."""
    threads = get_all_threads_from_dynamodb()
    for thread in threads:
        if len(thread.get("chat_log", [])) <= 1:
            delete_all_threads_from_dynamodb()