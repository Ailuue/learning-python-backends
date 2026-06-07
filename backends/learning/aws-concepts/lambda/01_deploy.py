import sys, os, io, zipfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client

lmb = client("lambda")

ROLE = "arn:aws:iam::000000000000:role/lambda-role"  # LocalStack ignores IAM; any ARN works

def zip_file(path: str) -> bytes:
    """Package a single .py file into a zip suitable for Lambda deployment."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(path, arcname="handler.py")
    return buf.getvalue()

handler_path = os.path.join(os.path.dirname(__file__), "functions", "hello", "handler.py")

# --- Create function ---
print("=== Creating Lambda function ===")
lmb.create_function(
    FunctionName="hello",
    Runtime="python3.11",
    Role=ROLE,
    Handler="handler.lambda_handler",
    Code={"ZipFile": zip_file(handler_path)},
    Timeout=10,
    MemorySize=128,
    Description="Greets a user by name",
)
print("Function 'hello' created")

# --- List functions ---
print("\n=== Listing functions ===")
for fn in lmb.list_functions()["Functions"]:
    print(f"  {fn['FunctionName']}  runtime={fn['Runtime']}  memory={fn['MemorySize']}MB")

# --- Get function config ---
print("\n=== Function configuration ===")
config = lmb.get_function_configuration(FunctionName="hello")
print(f"  Handler:     {config['Handler']}")
print(f"  Timeout:     {config['Timeout']}s")
print(f"  Last modified: {config['LastModified']}")

# --- Update function code (re-deploy) ---
print("\n=== Updating function code ===")
new_handler_code = """\
import json

def lambda_handler(event, context):
    name = event.get("name", "world")
    version = event.get("version", 2)
    return {
        "statusCode": 200,
        "body": json.dumps({"message": f"Hello v{version}, {name}!"}),
    }
"""
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as zf:
    zf.writestr("handler.py", new_handler_code)

lmb.update_function_code(FunctionName="hello", ZipFile=buf.getvalue())
print("Code updated")

# --- Delete ---
print("\n=== Deleting function ===")
lmb.delete_function(FunctionName="hello")
remaining = [f["FunctionName"] for f in lmb.list_functions()["Functions"]]
print(f"Remaining functions: {remaining}")
