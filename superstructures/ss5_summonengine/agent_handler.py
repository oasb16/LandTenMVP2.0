from typing import List, Dict, Any
from utils.gpt_call import call_gpt_agent
import json
import os
from uuid import uuid4

def process_agent_tag(chat_data: List[Dict[str, str]]) -> Dict[str, Any]:
    if not chat_data:
        raise ValueError("Chat data is empty.")

    formatted_messages = "\n".join(
        f"{msg['sender']} ({msg['timestamp']}): {msg['message']}"
        for msg in chat_data
    )

    system_prompt = (
        "You are a property maintenance expert. Given a list of chat messages between tenant and landlord, extract:\n\n"
        "- The likely job type (e.g. plumbing, electrical)\n"
        "- A description of the issue\n"
        "- The urgency (low, medium, high)\n"
        "- An estimated price range if possible\n\n"
        "Output as a JSON dictionary with keys: job_type, description, priority, price"
    )

    prompt_payload = f"{system_prompt}\n\nCHAT LOG:\n{formatted_messages}"

    gpt_response = call_gpt_agent([{"role": "system", "content": prompt_payload}])

    try:
        gpt_response_dict = json.loads(gpt_response)
    except json.JSONDecodeError:
        raise ValueError("GPT response is not valid JSON.")

    if not isinstance(gpt_response_dict, dict):
        raise ValueError("GPT response is not a dictionary.")

    expected_keys = {"job_type", "description", "priority", "price"}
    if not expected_keys.issubset(gpt_response_dict):
        raise ValueError(f"GPT response missing required keys: {expected_keys - gpt_response_dict.keys()}")

    # Optional: Log raw output in dev mode
    if os.getenv("DEV_MODE") == "true":
        log_file = f"logs/agent_responses_{uuid4()}.json"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "w") as f:
            json.dump(gpt_response_dict, f, indent=4)

    return gpt_response_dict