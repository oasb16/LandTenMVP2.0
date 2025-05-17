import streamlit as st
import datetime
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

# Collaborative Canvas (Placeholder for now)
def collaborative_canvas():
    st.write("🖌 Collaborative Canvas")
    st.info("Collaborative Canvas feature is under development. Stay tuned!")

# Calendar Scheduler
def calendar_scheduler():
    st.write("📅 Calendar Scheduler")

    # Google Calendar API setup
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None

    # Load credentials from token.pickle if available
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, prompt user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # User input for event details
    selected_date = st.date_input("Select a date for scheduling:", min_value=datetime.date.today())
    event_details = st.text_area("Add event details:", placeholder="E.g., Meeting with contractor at 3 PM")
    start_time = st.time_input("Start Time:")
    end_time = st.time_input("End Time:")

    if st.button("Schedule Event"):
        event = {
            'summary': event_details,
            'start': {
                'dateTime': f"{selected_date}T{start_time}:00",
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': f"{selected_date}T{end_time}:00",
                'timeZone': 'UTC',
            },
        }

        try:
            event = service.events().insert(calendarId='primary', body=event).execute()
            st.success(f"Event created: {event.get('htmlLink')}")
        except Exception as e:
            st.error(f"An error occurred: {e}")

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