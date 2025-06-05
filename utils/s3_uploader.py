import json
import logging
import streamlit as st
from botocore.exceptions import ClientError

import boto3
s3_client = boto3.client("s3",
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
    region_name=st.secrets["AWS_REGION"]
)

def upload_incident_to_s3(incident_id, data):
    try:
        file_key = f"incidents/{incident_id}.json"

        s3_client.put_object(
            Bucket=st.secrets["S3_BUCKET"],
            Key=file_key,
            Body=json.dumps(data, indent=2),
            ContentType="application/json"
        )

        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": st.secrets["S3_BUCKET"], "Key": file_key},
            ExpiresIn=300
        )

        st.success(f"✅ Incident uploaded: [view]({presigned_url})", icon="🪣")
        return presigned_url

    except ClientError as e:
        logging.error(f"S3 Upload Error: {e.response['Error']['Message']}")
        st.error(f"S3 Upload Error: {e.response['Error']['Message']}")
        return None

def upload_job_to_s3(job_id, data):
    try:
        file_key = f"jobs/{job_id}.json"

        s3_client.put_object(
            Bucket=st.secrets["S3_BUCKET"],
            Key=file_key,
            Body=json.dumps(data, indent=2),
            ContentType="application/json"
        )

        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": st.secrets["S3_BUCKET"], "Key": file_key},
            ExpiresIn=300
        )

        st.success(f"✅ Job uploaded: [view]({presigned_url})", icon="🛠️")
        return presigned_url

    except ClientError as e:
        logging.error(f"S3 Upload Error: {e.response['Error']['Message']}")
        st.error(f"S3 Upload Error: {e.response['Error']['Message']}")
        return None
