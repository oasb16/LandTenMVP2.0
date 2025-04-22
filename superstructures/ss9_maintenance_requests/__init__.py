import streamlit as st
import os
from datetime import datetime

def handle_maintenance_requests():
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

        # Save the request details
        request_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        request_data = {
            "id": request_id,
            "description": description,
            "urgency": urgency,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Save photo if uploaded
        if photo:
            photo_path = f"maintenance_photos/{request_id}_{photo.name}"
            os.makedirs("maintenance_photos", exist_ok=True)
            with open(photo_path, "wb") as f:
                f.write(photo.read())
            request_data["photo_path"] = photo_path

        # Simulate saving to a database or file
        os.makedirs("maintenance_requests", exist_ok=True)
        with open(f"maintenance_requests/{request_id}.txt", "w") as f:
            f.write(str(request_data))

        # Notify landlord and contractor (simulated)
        st.success(f"Maintenance request submitted successfully! Request ID: {request_id}")
        st.info("Landlord and contractor have been notified.")