import streamlit as st
import os
import sqlite3
from datetime import datetime
from streamlit_app import log_success

def initialize_database():
    conn = sqlite3.connect("maintenance_requests.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS requests (
        id TEXT PRIMARY KEY,
        description TEXT NOT NULL,
        urgency TEXT NOT NULL,
        photo_path TEXT,
        status TEXT DEFAULT 'pending',
        timestamp TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

def is_duplicate_request(description):
    conn = sqlite3.connect("maintenance_requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM requests WHERE description = ?", (description,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def handle_maintenance_requests():
    initialize_database()
    st.subheader("Submit Maintenance Request")

    # Input fields for maintenance request
    description = st.text_area("Describe the issue", placeholder="E.g., Leaking faucet in the kitchen")
    photo = st.file_uploader("Upload a photo (optional)", type=["jpg", "png", "jpeg"])
    urgency = st.selectbox("Urgency Level", ["Low", "Medium", "High"], index=1)

    # Submit button
    if st.button("Submit Request"):
        if not description:
            st.error("Description is required to submit a maintenance request.")
            return

        if is_duplicate_request(description):
            st.warning("A similar maintenance request already exists.")
            return

        # Save the request details
        request_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        request_data = {
            "id": request_id,
            "description": description,
            "urgency": urgency,
            "status": "pending",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Save photo if uploaded
        if photo:
            photo_path = f"maintenance_photos/{request_id}_{photo.name}"
            os.makedirs("maintenance_photos", exist_ok=True)
            with open(photo_path, "wb") as f:
                f.write(photo.read())
            request_data["photo_path"] = photo_path

        # Save to database
        conn = sqlite3.connect("maintenance_requests.db")
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO requests (id, description, urgency, photo_path, status, timestamp)
                          VALUES (:id, :description, :urgency, :photo_path, :status, :timestamp)''', request_data)
        conn.commit()
        conn.close()

        # Notify landlord and contractor (simulated)
        log_success(f"Maintenance request submitted successfully! Request ID: {request_id}")
        st.info("Landlord and contractor have been notified.")