import sys
import os
import io
import zipfile
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client

lmb = client("lambda")
s3  = client("s3")
ROLE   = "arn:aws:iam::000000000000:role/lambda-role"
BUCKET = "uploads-trigger-demo"
FN     = "s3-processor"

def zip_file(path: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(path, arcname="handler.py")
    return buf.getvalue()

handler_path = os.path.join(os.path.dirname(__file__), "functions", "s3_processor", "handler.py")

# --- Deploy the function ---
print("=== Deploying s3-processor Lambda ===")
fn = lmb.create_function(
    FunctionName=FN,
    Runtime="python3.11",
    Role=ROLE,
    Handler="handler.lambda_handler",
    Code={"ZipFile": zip_file(handler_path)},
    Timeout=15,
)
fn_arn = fn["FunctionArn"]
print(f"Function ARN: {fn_arn}")

# --- Create S3 bucket ---
s3.create_bucket(Bucket=BUCKET)
print(f"Bucket '{BUCKET}' created")

# --- Grant S3 permission to invoke the Lambda ---
# Without this, S3 can't call your function — even in LocalStack.
lmb.add_permission(
    FunctionName=FN,
    StatementId="allow-s3-invoke",
    Action="lambda:InvokeFunction",
    Principal="s3.amazonaws.com",
    SourceArn=f"arn:aws:s3:::{BUCKET}",
)
print("Permission granted: S3 can invoke the function")

# --- Set up S3 event notification ---
# Trigger the function on any ObjectCreated event (PUT, POST, COPY, multipart upload).
# Prefix/suffix filters let you target specific folders or file types.
s3.put_bucket_notification_configuration(
    Bucket=BUCKET,
    NotificationConfiguration={
        "LambdaFunctionConfigurations": [
            {
                "LambdaFunctionArn": fn_arn,
                "Events": ["s3:ObjectCreated:*"],
                "Filter": {
                    "Key": {"FilterRules": [{"Name": "suffix", "Value": ".csv"}]}
                },
            }
        ]
    },
)
print("S3 notification configured: .csv uploads → Lambda")

# --- Upload files to trigger the function ---
print("\n=== Uploading files ===")
time.sleep(2)  # give LocalStack a moment to wire the trigger

s3.put_object(Bucket=BUCKET, Key="data/users.csv", Body="id,name\n1,Alice")
print("  Uploaded data/users.csv  ← should trigger Lambda")
time.sleep(1)

s3.put_object(Bucket=BUCKET, Key="images/photo.jpg", Body=b"(fake image)")
print("  Uploaded images/photo.jpg ← should NOT trigger (not .csv)")
time.sleep(1)

s3.put_object(Bucket=BUCKET, Key="reports/q4.csv", Body="month,revenue\nQ4,90000")
print("  Uploaded reports/q4.csv  ← should trigger Lambda")

# The Lambda prints to stdout — in LocalStack you'd see logs via:
#   docker logs $(docker ps -q --filter "name=localstack")
print("\nCheck LocalStack container logs to see Lambda output:")
print("  docker logs $(docker ps -q --filter 'name=localstack') 2>&1 | grep s3_processor")

# --- Cleanup ---
time.sleep(2)
for obj in s3.list_objects_v2(Bucket=BUCKET).get("Contents", []):
    s3.delete_object(Bucket=BUCKET, Key=obj["Key"])
s3.delete_bucket(Bucket=BUCKET)
lmb.delete_function(FunctionName=FN)
print("\nCleaned up.")
