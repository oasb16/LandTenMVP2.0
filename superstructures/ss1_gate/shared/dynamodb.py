from datetime import datetime
import boto3
import os
import streamlit as st

# === AWS Credentials from secrets.toml
try:
    os.environ["AWS_ACCESS_KEY"] = st.secrets["AWS_ACCESS_KEY"]
    os.environ["AWS_SECRET_ACCESS_KEY"] = st.secrets["AWS_SECRET_ACCESS_KEY"]
    os.environ["AWS_REGION"] = st.secrets.get("AWS_REGION", "us-east-1")
except KeyError as e:
    st.error(f"Missing AWS credential in secrets: {e}")
    st.stop()

# === Initialize DynamoDB Resource
try:
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("landten_users")
except Exception as e:
    st.error(f"Failed to initialize DynamoDB: {e}")
    st.stop()

def save_user_profile(profile: dict):
    """
    Save or update a user profile in the DynamoDB table.
    This function ensures that required fields are validated and handles errors gracefully.
    """
    # Validate required fields
    required_fields = ["user_id", "name", "email"]
    for field in required_fields:
        if field not in profile:
            raise ValueError(f"Missing required field: {field}")

    # Add timestamps
    now = datetime.utcnow().isoformat()
    profile["created_at"] = profile.get("created_at", now)
    profile["updated_at"] = now

    try:
        # Save the profile to the table
        table.put_item(Item=profile)
    except Exception as e:
        # Log the error and re-raise
        print(f"Error saving user profile: {e}")
        raise

# Update write_user_profile to use save_user_profile for better consistency
def write_user_profile(profile: dict):
    """
    Deprecated: Use save_user_profile instead.
    """
    print("write_user_profile is deprecated. Use save_user_profile instead.")
    save_user_profile(profile)
