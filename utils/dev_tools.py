# utils/dev_tools.py

import streamlit as st
import os

def dev_seed_expander():
    with st.expander("🧪 Test Data Tools", expanded=False):
        if st.button("🆕 Create Dummy Incidents + Jobs"):
            try:
                from scripts.seed_test_data import seed_incidents, seed_jobs_from_incidents
                seed_incidents(n=3)
                seed_jobs_from_incidents()
                st.success("Dummy incidents and jobs created.")
                # st.rerun()
            except Exception as e:
                st.error(f"Error generating test data: {e}")

        if st.button("🗑️ Delete All Dummy Incidents + Jobs"):
            try:
                for file in ["logs/incidents.json", "logs/jobs.json"]:
                    if os.path.exists(file):
                        os.remove(file)
                        st.success(f"Deleted {file}")
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting test data: {e}")
