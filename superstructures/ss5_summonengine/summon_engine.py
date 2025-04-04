
import uuid
import json
from datetime import datetime
from utils.gpt_call import call_gpt

def run_summon_engine(chat_history, user_input, persona, thread_id):
    if "@agent" not in user_input.lower():
        return {"message": "No GPT agent triggered.", "actions": None}

    prompt = build_prompt(chat_history, user_input, persona)
    gpt_response = call_gpt(prompt)

    response = {
        "message": gpt_response,
        "actions": build_actions(persona)
    }

    log_path = f"logs/agent_responses_{thread_id}.json"
    with open(log_path, "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "input": user_input,
            "persona": persona,
            "response": response
        }) + "\n")

    return response

def build_prompt(chat_history, user_input, persona):
    return [
        {"role": "system", "content": f"You are an assistant helping the {persona} on a rental coordination platform."},
        *[{"role": "user", "content": msg} for msg in chat_history],
        {"role": "user", "content": user_input}
    ]

def build_actions(persona):
    action_map = {
        "tenant": [{"label": "Create Incident", "visible_to": "tenant"}],
        "landlord": [{"label": "Approve", "visible_to": "landlord"}],
        "contractor": [{"label": "Mark Complete", "visible_to": "contractor"}]
    }
    return action_map.get(persona, None)
