import streamlit as st
import os
from datetime import datetime

def assign_tasks_to_contractors():
    st.subheader("Assign Tasks to Contractors")

    # Input fields for task assignment
    task_description = st.text_area("Task Description", placeholder="E.g., Fix the leaking faucet in Apartment 3B")
    contractor = st.selectbox("Select Contractor", ["Contractor A", "Contractor B", "Contractor C"])
    deadline = st.date_input("Deadline", min_value=datetime.now().date())

    # Submit button
    if st.button("Assign Task"):
        if not task_description or not contractor:
            st.error("Task description and contractor selection are required.")
            return

        # Save the task details
        task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        task_data = {
            "id": task_id,
            "description": task_description,
            "contractor": contractor,
            "deadline": deadline.strftime('%Y-%m-%d'),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Simulate saving to a database or file
        os.makedirs("assigned_tasks", exist_ok=True)
        with open(f"assigned_tasks/{task_id}.txt", "w") as f:
            f.write(str(task_data))

        # Notify contractor (simulated)
        st.success(f"Task assigned successfully! Task ID: {task_id}")
        st.info(f"Contractor {contractor} has been notified.")