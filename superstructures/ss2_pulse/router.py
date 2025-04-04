import streamlit as st
from superstructures.ss3_echo import run_tenant_view
# from superstructures.ss4_root.landlord_view import run_landlord_view
# from superstructures.ss4_root.contractor_view import run_contractor_view
from superstructures.tracker import show_tracker

def route_user(persona: str):
    if persona == "tenant":
        run_tenant_view()
    elif persona == "landlord":
        run_tenant_view()
    elif persona == "contractor":
        run_tenant_view()
    elif persona == "admin":
        show_tracker()
    else:
        st.error("Invalid persona.")
