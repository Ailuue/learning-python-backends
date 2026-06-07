import boto3

ENDPOINT = "http://localhost:4566"
REGION = "us-east-1"
_CREDS = {"aws_access_key_id": "test", "aws_secret_access_key": "test"}


def client(service: str):
    return boto3.client(service, endpoint_url=ENDPOINT, region_name=REGION, **_CREDS)


def resource(service: str):
    return boto3.resource(service, endpoint_url=ENDPOINT, region_name=REGION, **_CREDS)
