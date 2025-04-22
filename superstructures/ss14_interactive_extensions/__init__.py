import streamlit as st
import datetime
import matplotlib.pyplot as plt

# Collaborative Canvas (Placeholder for now)
def collaborative_canvas():
    st.write("🖌 Collaborative Canvas")
    st.info("Collaborative Canvas feature is under development. Stay tuned!")

# Calendar Scheduler
def calendar_scheduler():
    st.write("📅 Calendar Scheduler")
    selected_date = st.date_input("Select a date for scheduling:", min_value=datetime.date.today())
    event_details = st.text_area("Add event details:", placeholder="E.g., Meeting with contractor at 3 PM")
    if st.button("Schedule Event"):
        st.success(f"Event scheduled for {selected_date}: {event_details}")

# Performance Insights
def performance_insights():
    st.write("📈 Performance Insights")

    # Simulated data for insights
    insights = {
        "Property A": "High occupancy, consider rent increase.",
        "Property B": "Maintenance overdue, prioritize repairs.",
        "Property C": "Low tenant satisfaction, investigate complaints."
    }

    for property, insight in insights.items():
        st.write(f"- **{property}**: {insight}")

    # Example visualization
    st.write("### Occupancy Rate Comparison")
    properties = ["Property A", "Property B", "Property C"]
    occupancy_rates = [95, 85, 80]

    fig, ax = plt.subplots()
    ax.bar(properties, occupancy_rates, color=['green', 'orange', 'red'])
    ax.set_ylabel("Occupancy Rate (%)")
    ax.set_title("Occupancy Rate by Property")
    st.pyplot(fig)

# Main function to show interactive extensions
def show_interactive_extensions():
    st.subheader("Interactive Extensions")

    # Collaborative Canvas
    collaborative_canvas()

    # Calendar Scheduler
    calendar_scheduler()

    # Performance Insights
    performance_insights()