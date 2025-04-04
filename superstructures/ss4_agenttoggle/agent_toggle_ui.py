import streamlit as st

def run_agent_toggle():
    if "summon_triggered" not in st.session_state:
        st.session_state["summon_triggered"] = False

    if st.button("🔮 Summon Agent" if not st.session_state["summon_triggered"] else "❌ Cancel Agent"):
        st.session_state["summon_triggered"] = not st.session_state["summon_triggered"]

    st.markdown(
        f"**Agent Status:** {'🟢 Active' if st.session_state['summon_triggered'] else '⚪ Inactive'}"
    )
