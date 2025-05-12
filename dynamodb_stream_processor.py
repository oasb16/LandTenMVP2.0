import boto3
import json
import logging

# Initialize DynamoDB and WebSocket client
user_table = boto3.resource('dynamodb').Table('UserTable')  # Replace 'UserTable' with your actual table name
websocket_client = boto3.client('apigatewaymanagementapi', endpoint_url="https://your-websocket-endpoint")  # Replace with your WebSocket endpoint

def lambda_handler(event, context):
    """AWS Lambda function to process DynamoDB Stream events."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        # Process each record in the event
        for record in event['Records']:
            if record['eventName'] in ['INSERT', 'MODIFY']:
                # Extract the new image from the DynamoDB Stream record
                new_image = record['dynamodb']['NewImage']
                thread_id = new_image.get('thread_id', {}).get('S', 'unknown')
                chat_log = new_image.get('chat_log', {}).get('L', [])

                # Log the processed record
                logging.info(f"Processed record for thread_id: {thread_id}")
                logging.info(f"Chat log: {json.dumps(chat_log)}")

                # Query the User table to fetch users associated with the thread
                response = user_table.scan(
                    FilterExpression="contains(threads, :thread_id)",
                    ExpressionAttributeValues={":thread_id": thread_id}
                )
                users = response.get('Items', [])

                # Push notifications to WebSocket clients
                for user in users:
                    connection_id = user.get('connection_id')  # Ensure connection_id is stored in the User table
                    if connection_id:
                        try:
                            websocket_client.post_to_connection(
                                ConnectionId=connection_id,
                                Data=json.dumps({
                                    "type": "notification",
                                    "message": f"Thread {thread_id} has been updated.",
                                    "chat_log": chat_log
                                })
                            )
                            logging.info(f"Notification sent to connection_id: {connection_id}")
                        except Exception as e:
                            logging.error(f"Failed to send notification to connection_id {connection_id}: {str(e)}")

                # Add custom logic here to push updates to WebSocket server or other services

    except Exception as e:
        logging.error(f"Error processing DynamoDB Stream event: {str(e)}")
        raise e