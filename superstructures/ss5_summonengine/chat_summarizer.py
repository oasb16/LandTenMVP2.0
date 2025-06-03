import os
import json
from utils.gpt_call import call_gpt_model

def summarize_chat_thread(incident_id: str) -> str:
    path = f"logs/chat_thread_{incident_id}.json"
    if not os.path.exists(path):
        return "No chat history found."

    try:
        with open(path, "r") as f:
            messages = json.load(f)

        # Format the chat log for summarization
        formatted_chat = "\n".join(
            f"{msg['sender']}: {msg['message']}" for msg in messages if msg.get("message")
        )

        prompt = (
            "You are an intelligent assistant helping summarize maintenance incident conversations.\n"
            "Given the following chat between a tenant, landlord, agent, and contractor, provide a concise summary of the issue and next steps if any.\n\n"
            f"{formatted_chat}\n\n"
            "Summary:"
        )

        return call_gpt_model(prompt)
    except Exception as e:
        return f"Error summarizing thread: {str(e)}"
