from typing import List, Dict, Any
from utils.gpt_call import call_gpt_model
from utils.logger import log_agent_event
import time

def process_agent_tag(chat_data: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Accepts chat_data and returns GPT-suggested job metadata.
    """
    start = time.time()

    if not chat_data:
        return {"job_type": "", "description": "", "priority": "", "price": None}

    # Format chat log for GPT prompt
    formatted_chat = "\n".join(
        f"{msg['sender']} ({msg['timestamp']}): {msg['message']}"
        for msg in chat_data
    )

    # System prompt
    system_prompt = (
        "You are a property maintenance expert.\n\n"
        "Analyze the following tenant-landlord chat log and extract:\n"
        "- The likely job type (e.g., plumbing, electrical)\n"
        "- A description of the problem\n"
        "- The urgency (low, medium, high)\n"
        "- An estimated price if appropriate\n\n"
        "Output only a JSON dictionary with keys:\n"
        "job_type, description, priority, price"
    )

    prompt_payload = f"{system_prompt}\n\nCHAT LOG:\n{formatted_chat}"

    try:
        result = call_gpt_model(prompt_payload)
        latency = (time.time() - start) * 1000  # ms

        log_agent_event({
            "source": "agent_handler.process_agent_tag",
            "incident_id": None,  # pass into function or extract
            "job_id": result.get("job_id"),
            "latency_ms": int(latency),
            "response_summary": {
                "job_type": result.get("job_type"),
                "priority": result.get("priority"),
                "description": result.get("description"),
            },
            "actions_proposed": [],  # none at this step
            "actions_executed": [],
            "autonomy": False
        })

        if isinstance(result, dict) and all(k in result for k in ["job_type", "description", "priority", "price"]):
            return result
        else:
            # Optional logging stub — replace with actual logger if needed
            print("⚠️ Malformed GPT response:", result)
            return {"job_type": "", "description": "", "priority": "", "price": None}
    except Exception as e:
        # Optional logging stub — replace with actual logger if needed
        print(f"❌ GPT call failed: {e}")
        return {"job_type": "", "description": "", "priority": "", "price": None}