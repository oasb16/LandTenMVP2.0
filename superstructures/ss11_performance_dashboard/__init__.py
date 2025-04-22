import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

def show_performance_dashboard():
    st.subheader("Property Performance Metrics")

    # Simulated data for performance metrics
    data = {
        "Property": ["Property A", "Property B", "Property C"],
        "Rent Collection (%)": [95, 88, 92],
        "Occupancy Rate (%)": [90, 85, 80],
        "Pending Maintenance": [2, 5, 3]
    }

    df = pd.DataFrame(data)

    # Display data as a table
    st.write("### Performance Overview")
    st.dataframe(df, use_container_width=True)

    # Rent Collection Bar Chart
    st.write("### Rent Collection")
    fig, ax = plt.subplots()
    ax.bar(df["Property"], df["Rent Collection (%)"], color="green")
    ax.set_ylabel("Percentage")
    ax.set_title("Rent Collection by Property")
    st.pyplot(fig)

    # Occupancy Rate Line Chart
    st.write("### Occupancy Rate")
    fig, ax = plt.subplots()
    ax.plot(df["Property"], df["Occupancy Rate (%)"], marker="o", linestyle="--", color="blue")
    ax.set_ylabel("Percentage")
    ax.set_title("Occupancy Rate by Property")
    st.pyplot(fig)

    # Pending Maintenance Pie Chart
    st.write("### Pending Maintenance Requests")
    fig, ax = plt.subplots()
    ax.pie(df["Pending Maintenance"], labels=df["Property"], autopct="%1.1f%%", startangle=90, colors=["red", "orange", "yellow"])
    ax.set_title("Pending Maintenance Distribution")
    st.pyplot(fig)