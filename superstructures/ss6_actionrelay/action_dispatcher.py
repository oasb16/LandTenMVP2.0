import streamlit as st
from utils.logger import log_info
from ss6_actionrelay.job_manager import (
    assign_job, accept_job, reject_job, mark_job_completed
)
from ss6_actionrelay.incident_manager import approve_incident
from utils.message_bundler import bundle_agent_and_action
from utils.db import load_chat_log, append_chat_message

def handle_action(label: str, context: dict):
    """Handle actions triggered from chat UI."""
    import streamlit as st

    actor = context.get("actor", st.session_state.get("user_id", "unknown"))

    try:
        if label == "Assign to Contractor":
            assign_job(context["job_id"], context["contractor_id"])
            log_info(f"Assigned job {context['job_id']} to {context['contractor_id']}")
            result_summary = f"Job {context['job_id']} assigned to contractor."

        elif label == "Accept Job":
            accept_job(context["job_id"], actor)
            log_info(f"Job {context['job_id']} accepted by {actor}")
            result_summary = f"Job {context['job_id']} accepted by {actor}."

        elif label == "Reject Job":
            reject_job(context["job_id"], actor)
            log_info(f"Job {context['job_id']} rejected by {actor}")
            result_summary = f"Job {context['job_id']} rejected by {actor}."

        elif label == "Approve Incident":
            approve_incident(context["incident_id"])
            log_info(f"Incident {context['incident_id']} approved")
            result_summary = f"Incident {context['incident_id']} approved."

        elif label == "Mark Completed":
            mark_job_completed(context["job_id"])
            log_info(f"Job {context['job_id']} marked as completed")
            result_summary = f"Job {context['job_id']} marked as completed."

        else:
            st.error(f"Unknown action: {label}")
            return

        # Load last agent message from chat
        chat_log = load_chat_log(context["incident_id"])
        last_agent_msg = next((msg for msg in reversed(chat_log) if msg["sender"] == "agent" and "actions" in msg), None)

        if last_agent_msg:
            bundled = bundle_agent_and_action(
                agent_msg=last_agent_msg,
                user_action=label,
                result_summary=result_summary
            )
            append_chat_message(context["incident_id"], bundled)

    except KeyError as e:
        log_info(f"Missing context key for action {label}: {str(e)}")
        st.error(f"Missing context key: {str(e)}")

    except Exception as ex:
        log_info(f"Action handler error [{label}]: {str(ex)}")
        st.error(f"Error handling action [{label}]: {str(ex)}")