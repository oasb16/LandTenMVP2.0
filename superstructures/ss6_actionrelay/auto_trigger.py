from utils.db import load_chat_log, append_chat_message, get_available_contractors
from ss6_actionrelay.action_dispatcher import handle_action
from utils.logger import log_agent_event
import traceback

def auto_execute_actions(incident_id: str):
    """
    Scan recent agent messages from incident chat thread and auto-execute actions
    if state conditions safely allow.
    """
    try:
        chat_log = load_chat_log(incident_id)
        if not chat_log:
            return

        recent_messages = chat_log[-5:]  # only last N entries

        proposed_actions = []
        executed_actions = []

        for msg in recent_messages:
            if msg.get("sender") != "agent" or "actions" not in msg:
                continue

            for action in msg["actions"]:
                label = action.get("label")
                if not label:
                    continue

                proposed_actions.append(label)

                # Sample rule: auto-assign if only one contractor
                if label == "Assign to Contractor":
                    contractors = get_available_contractors()
                    if len(contractors) == 1:
                        context = {
                            "incident_id": incident_id,
                            "contractor_id": contractors[0]["contractor_id"],
                            "job_id": msg.get("job_id", None),
                            "actor": "system"
                        }
                        handle_action("Assign to Contractor", context)
                        append_chat_message(incident_id, {
                            "sender": "system",
                            "message": f"✅ Auto-executed: {label}"
                        })
                        executed_actions.append(label)

                # Add more conditionals here for other auto-executable actions

        log_agent_event({
            "source": "auto_trigger.auto_execute_actions",
            "incident_id": incident_id,
            "job_id": None,  # inferred_job_id can be added if available
            "latency_ms": 0,
            "response_summary": {},
            "actions_proposed": proposed_actions,
            "actions_executed": executed_actions,
            "autonomy": True
        })

    except Exception as e:
        print(f"[AutoTrigger] Failed to auto-execute: {e}")
        traceback.print_exc()