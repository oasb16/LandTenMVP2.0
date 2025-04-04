import streamlit as st

def run_personagate():
    st.title("🔐 PersonaGate Login")

    if "role" not in st.session_state:
        st.session_state["role"] = None

    persona = st.selectbox("Select your persona", ["tenant", "landlord", "contractor"])

    if st.button("Confirm Persona"):
        st.session_state["role"] = persona
        st.success(f"Persona set: {persona}")
        st.experimental_rerun()
