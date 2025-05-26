from typing import List, Dict, Any
from utils.gpt_call import call_gpt_model

def process_agent_tag(chat_data: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Accepts chat_data and returns GPT-suggested job metadata.
    """
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