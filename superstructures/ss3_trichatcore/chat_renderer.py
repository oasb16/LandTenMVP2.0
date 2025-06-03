from ss5_summonengine.chat_summarizer import summarize_chat_thread
from utils.db import get_chat_thread
import streamlit as st

def render_chat_thread(chat_data: list, incident_id: str):
    """Render chat history with role-scoped action buttons and GPT summary."""
    # Only show summary if tenant or contractor
    if st.session_state.get("persona") in ("tenant", "contractor"):
        chat_thread = get_chat_thread(incident_id)
        if chat_thread:
            summary = summarize_chat_thread(incident_id)
            if summary and "⚠️" not in summary:
                st.info(f"**🧠 Assistant Summary:**\n\n{summary}")

    # Render chat data normally
    for entry in chat_data:
        st.write(f"**{entry['sender']}**: {entry['message']}")

        if "actions" in entry:
            for i, action in enumerate(entry["actions"]):
                if action.get("visible_to") == st.session_state.get("persona"):
                    if st.button(action["label"], key=f"{entry['message']}_{i}"):
                        from superstructures.ss6_actionrelay.action_dispatcher import handle_action
                        handle_action(action["label"], context={"source_message": entry["message"]})