# superstructures/tracker.py
import streamlit as st
import pandas as pd
from datetime import datetime

def show_tracker():
    st.title("🗂 LandTen MVP Protocol Tracker")

    # Superstructure Metadata
    superstructures = [
        ("Gate", "SS1: AWS Cognito Authentication", "ss1_gate"),
        ("Pulse", "SS2: Persona-Based Dashboard Router", "ss2_pulse"),
        ("Echo", "SS3: Tenant GPT Chat + Incident Summary", "ss3_echo"),
        ("Root", "SS4: Incident Queue Middleware", "ss4_root"),
        ("View", "SS5: Landlord Incident Dashboard", "ss5_view"),
        ("Cast", "SS6: Contractor Ticket Creation", "ss6_cast"),
        ("Bind", "SS7: Contractor Response + Ledger", "ss7_bind"),
        ("Sync", "SS8: Scheduling Interface", "ss8_sync"),
        ("Seal", "SS9: Completion & Verification", "ss9_seal"),
        ("Core", "SS10: Streamlit Shell + Payment Placeholder", "ss10_core"),
    ]

    # Function to read status from .status files
    def read_status(path):
        try:
            with open(path, "r") as f:
                content = f.read().strip()
                if "|" in content:
                    status, ts = content.split("|")
                    return status.strip(), ts.strip()
                return content.strip(), "-"
        except FileNotFoundError:
            return "Not Started", "-"

    # Populate Status Table
    statuses = []
    timestamps = []

    for _, _, folder in superstructures:
        path = f"./superstructures/{folder}/.status"
        status, ts = read_status(path)
        statuses.append(status)
        timestamps.append(ts)

    df = pd.DataFrame({
        "Protocol": [x[0] for x in superstructures],
        "Superstructure": [x[1] for x in superstructures],
        "Status": statuses,
        "Last Updated": timestamps,
    })

    st.dataframe(df, use_container_width=True)
