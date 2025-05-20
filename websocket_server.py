import asyncio
import websockets
import boto3
import json
import logging
import jwt
from jwt.exceptions import InvalidTokenError
from botocore.exceptions import ClientError
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize AWS clients
dynamodb = boto3.client('dynamodb',
                        aws_access_key_id="<AWS_ACCESS_KEY>",
                        aws_secret_access_key="<AWS_SECRET_ACCESS_KEY>",
                        region_name="<AWS_REGION>")

# Secret key for JWT authentication
JWT_SECRET = "your_jwt_secret_key"
JWT_ALGORITHM = "HS256"

# Mapping of thread IDs to connected WebSocket clients
connected_clients = {}

# Enhanced error handling and logging for WebSocket server and DynamoDB Streams
def log_error(context, error):
    """Log detailed error information."""
    logging.error(f"Error in {context}: {str(error)}")
    logging.error(traceback.format_exc())

def log_popover(context, error):
    """Log detailed error information."""
    logging.error(f"Error in {context}: {str(error)}")
    logging.error(traceback.format_exc())

def log_success(context, info):
    """Log detailed error information."""
    logging.info(f"Error in {context}: {str(info)}")
    logging.info(traceback.format_exc())


def authenticate_client(token):
    """Authenticate WebSocket client using JWT."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload  # Return decoded payload if valid
    except InvalidTokenError:
        return None

def process_dynamodb_stream(record):
    """Process a single DynamoDB stream record."""
    if record['eventName'] == 'INSERT' or record['eventName'] == 'MODIFY':
        new_image = record['dynamodb']['NewImage']
        chat_log = new_image.get('chat_log', {}).get('L', [])
        thread_id = new_image.get('thread_id', {}).get('S', 'unknown')
        return {
            "thread_id": thread_id,
            "chat_log": chat_log
        }
    return None

async def dynamodb_stream_listener(websocket, thread_id):
    """Listen to DynamoDB Streams with enhanced error handling."""
    try:
        response = dynamodb.describe_table(TableName="<DYNAMODB_TABLE>")
        stream_arn = response['Table']['LatestStreamArn']

        stream_response = dynamodb.get_records(StreamArn=stream_arn)
        for record in stream_response['Records']:
            update = process_dynamodb_stream(record)
            if update and update["thread_id"] == thread_id:
                for client in connected_clients.get(thread_id, []):
                    await client.send(json.dumps(update))
    except ClientError as e:
        log_error("DynamoDB Stream ClientError", e)
    except Exception as e:
        log_error("DynamoDB Stream Listener", e)

async def websocket_handler(websocket, path):
    """Handle WebSocket connections with enhanced error handling."""
    logging.info("New WebSocket connection established.")
    try:
        # Receive authentication token from client
        token = await websocket.recv()
        user_data = authenticate_client(token)
        if not user_data:
            await websocket.close(code=4001, reason="Unauthorized")
            logging.warning("Unauthorized WebSocket connection attempt.")
            return

        thread_id = user_data.get("thread_id")
        if thread_id not in connected_clients:
            connected_clients[thread_id] = []
        connected_clients[thread_id].append(websocket)

        logging.info(f"Client connected to thread: {thread_id}")

        while True:
            await dynamodb_stream_listener(websocket, thread_id)
            await asyncio.sleep(1)  # Polling interval

    except websockets.ConnectionClosed as e:
        log_error("WebSocket Connection", e)
    except Exception as e:
        log_error("WebSocket Handler", e)
    finally:
        # Remove client from connected_clients
        if thread_id in connected_clients:
            connected_clients[thread_id].remove(websocket)
            if not connected_clients[thread_id]:
                del connected_clients[thread_id]

# Start WebSocket server
start_server = websockets.serve(websocket_handler, "localhost", 8765)

logging.info("Starting WebSocket server on ws://localhost:8765")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()