import streamlit as st

def extract_persona():
    query_params = st.query_params

    # Primary source: query string
    if "persona" in query_params:
        return query_params["persona"][0]

    # Fallback: use stored session state or default
    if "persona" in st.session_state:
        return st.session_state["persona"]

    return "tenant"  # Default persona
