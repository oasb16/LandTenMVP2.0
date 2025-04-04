import streamlit as st
from .chat_handler import get_gpt_reply
from .incident_writer import save_incident
from .utils import enforce_word_limit
import uuid
from datetime import datetime

def run_tenant_view():
    st.title("Tenant View")
    st.write("Welcome, tenant. You can now describe your issue.")


def run_echo():
    st.title("Tenant Dashboard")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    chat_container = st.container()
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Type your message here (max 20 words)...")
        submitted = st.form_submit_button("Send")

    if submitted and user_input:
        if not enforce_word_limit(user_input, 20):
            st.warning("Please limit your message to 20 words.")
            return
        st.session_state.chat.append({"role": "user", "content": user_input})

        messages = [{"role": msg["role"], "content": msg["content"]}
                    for msg in st.session_state.chat if msg["role"] == "user"]

        gpt_reply = get_gpt_reply(messages)
        st.session_state.chat.append({"role": "assistant", "content": gpt_reply})

        incident = {
            "id": f"incident_{uuid.uuid4()}",
            "full_chat": st.session_state.chat,
            "summary": gpt_reply,
            "keywords": [],
            "persona": "tenant",
            "priority": "medium",
            "timestamp": datetime.utcnow().isoformat()
        }

        save_incident(incident)
        st.success("Incident summary saved.")

    with chat_container:
        for msg in st.session_state.chat:
            role = "🧑 Tenant" if msg["role"] == "user" else "🤖 GPT"
            st.markdown(f"**{role}:** {msg['content']}")