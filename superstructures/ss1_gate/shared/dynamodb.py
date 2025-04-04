import boto3
from datetime import datetime

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("landten_users")

def write_user_profile(profile: dict):
    profile["updated_at"] = datetime.utcnow().isoformat()
    table.put_item(Item=profile)
