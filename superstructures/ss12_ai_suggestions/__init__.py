import streamlit as st
import random

def show_ai_suggestions():
    st.subheader("AI-Driven Suggestions")

    # Simulated property data for AI analysis
    properties = [
        {"name": "Property A", "rent_due": 2, "maintenance_overdue": 1, "occupancy_rate": 95},
        {"name": "Property B", "rent_due": 5, "maintenance_overdue": 3, "occupancy_rate": 85},
        {"name": "Property C", "rent_due": 0, "maintenance_overdue": 0, "occupancy_rate": 90},
    ]

    # Generate actionable suggestions based on property data
    suggestions = []
    for property in properties:
        if property["rent_due"] > 0:
            suggestions.append(f"Send rent reminders to tenants of {property['name']} (Overdue: {property['rent_due']} tenants).")
        if property["maintenance_overdue"] > 0:
            suggestions.append(f"Schedule maintenance for {property['name']} (Overdue tasks: {property['maintenance_overdue']}).")
        if property["occupancy_rate"] < 90:
            suggestions.append(f"Consider marketing strategies to improve occupancy for {property['name']} (Current rate: {property['occupancy_rate']}%).")

    # Display suggestions
    st.write("### Suggested Actions")
    for i, suggestion in enumerate(suggestions, start=1):
        st.write(f"{i}. {suggestion}")

    # Option to execute all suggestions
    if st.button("Execute All Suggestions"):
        st.success("All suggested actions have been executed.")
        st.info("Notifications have been sent to relevant parties.")