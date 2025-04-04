
import streamlit as st
from urllib.parse import urlparse

def extract_persona():
    query_params = st.query_params
    if "persona" in query_params:
        return query_params["persona"][0]
    path = urlparse(st.get_url()).path
    for p in ["tenant", "landlord", "contractor", "admin"]:
        if p in path:
            return p
    return "tenant"
