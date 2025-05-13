import boto3
from datetime import datetime

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("landten_users")

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
