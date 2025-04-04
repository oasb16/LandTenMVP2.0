import streamlit as st
from superstructures.ss2_pulse.router import route_user

def run_router():
    import streamlit as st
    persona = st.session_state.get("persona", None)
    if persona:
        route_user(persona)
    else:
        st.error("❌ No persona found in session state.")
