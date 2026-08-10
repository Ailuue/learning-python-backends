import sys
import os
import io
import zipfile
import json
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client

lmb = client("lambda")
ROLE = "arn:aws:iam::000000000000:role/lambda-role"

def zip_file(path: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(path, arcname="handler.py")
    return buf.getvalue()

handler_path = os.path.join(os.path.dirname(__file__), "functions", "hello", "handler.py")

lmb.create_function(
    FunctionName="hello",
    Runtime="python3.11",
    Role=ROLE,
    Handler="handler.lambda_handler",
    Code={"ZipFile": zip_file(handler_path)},
    Timeout=10,
)

# LocalStack may take a moment to spin up the container for the first invocation
time.sleep(2)

# --- Synchronous invocation (RequestResponse) ---
# The caller waits for the function to finish and gets the return value.
# Use for: API responses, real-time processing, anything where you need the result.
print("=== Synchronous invocation ===")
response = lmb.invoke(
    FunctionName="hello",
    InvocationType="RequestResponse",
    Payload=json.dumps({"name": "Alex"}),
)
payload = json.loads(response["Payload"].read())
status_code = response["StatusCode"]
print(f"  HTTP status:   {status_code}")       # 200 = invocation succeeded (not your function's statusCode)
print(f"  Function error: {response.get('FunctionError', 'none')}")
print(f"  Response body:  {payload}")

# --- Invoke with no payload ---
print("\n=== Invoke with no input ===")
response = lmb.invoke(FunctionName="hello", InvocationType="RequestResponse", Payload=b"{}")
print(f"  {json.loads(response['Payload'].read())}")

# --- Asynchronous invocation (Event) ---
# Lambda queues the event and returns immediately — you don't get the result.
# Use for: background jobs, notifications, anything fire-and-forget.
print("\n=== Asynchronous invocation ===")
response = lmb.invoke(
    FunctionName="hello",
    InvocationType="Event",
    Payload=json.dumps({"name": "async-caller"}),
)
print(f"  HTTP status: {response['StatusCode']}")  # 202 Accepted — function is queued, not yet run
print("  Fire-and-forget: no payload returned")

# --- Simulated error: function raises an exception ---
print("\n=== Function error handling ===")
error_code = """\
import json

def lambda_handler(event, context):
    if event.get("crash"):
        raise ValueError("Something went wrong!")
    return {"ok": True}
"""
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as zf:
    zf.writestr("handler.py", error_code)
lmb.update_function_code(FunctionName="hello", ZipFile=buf.getvalue())
time.sleep(1)

response = lmb.invoke(
    FunctionName="hello",
    InvocationType="RequestResponse",
    Payload=json.dumps({"crash": True}),
)
# StatusCode is still 200 — the invocation succeeded. The function error is in FunctionError.
error_payload = json.loads(response["Payload"].read())
print(f"  StatusCode:     {response['StatusCode']}")
print(f"  FunctionError:  {response.get('FunctionError')}")
print(f"  Error payload:  {error_payload}")

# --- Cleanup ---
lmb.delete_function(FunctionName="hello")
print("\nCleaned up.")
