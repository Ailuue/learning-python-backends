import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client

s3 = client("s3")
BUCKET = "objects-demo"
s3.create_bucket(Bucket=BUCKET)

# --- Upload ---
print("=== Uploading objects ===")
s3.put_object(Bucket=BUCKET, Key="config/settings.json", Body=json.dumps({"version": 1, "debug": True}))
s3.put_object(Bucket=BUCKET, Key="data/users.csv", Body="id,name\n1,Alice\n2,Bob")
s3.put_object(Bucket=BUCKET, Key="data/orders.csv", Body="id,user_id,total\n1,1,99.99")
print("Uploaded: config/settings.json, data/users.csv, data/orders.csv")

# --- List all ---
print("\n=== Listing all objects ===")
for obj in s3.list_objects_v2(Bucket=BUCKET).get("Contents", []):
    print(f"  {obj['Key']}  ({obj['Size']} bytes)")

# --- List with prefix (acts like a folder filter) ---
print("\n=== Listing with prefix 'data/' ===")
for obj in s3.list_objects_v2(Bucket=BUCKET, Prefix="data/").get("Contents", []):
    print(f"  {obj['Key']}")

# --- Download ---
print("\n=== Downloading an object ===")
body = s3.get_object(Bucket=BUCKET, Key="config/settings.json")["Body"].read().decode()
print(f"config/settings.json: {body}")

# --- Object metadata ---
print("\n=== Object metadata (head) ===")
head = s3.head_object(Bucket=BUCKET, Key="data/users.csv")
print(f"  Content-Length: {head['ContentLength']}")
print(f"  Last-Modified:  {head['LastModified']}")
print(f"  ETag:           {head['ETag']}")

# --- Copy ---
print("\n=== Copying an object ===")
s3.copy_object(
    Bucket=BUCKET,
    CopySource={"Bucket": BUCKET, "Key": "data/users.csv"},
    Key="backup/users.csv",
)
print("Copied data/users.csv → backup/users.csv")

# --- Delete single ---
print("\n=== Deleting a single object ===")
s3.delete_object(Bucket=BUCKET, Key="data/orders.csv")
print("Deleted data/orders.csv")

# --- Bulk delete ---
print("\n=== Bulk delete ===")
remaining_keys = [
    obj["Key"]
    for obj in s3.list_objects_v2(Bucket=BUCKET).get("Contents", [])
]
s3.delete_objects(
    Bucket=BUCKET,
    Delete={"Objects": [{"Key": k} for k in remaining_keys]},
)
print(f"Bulk deleted {len(remaining_keys)} objects")

# --- Cleanup ---
s3.delete_bucket(Bucket=BUCKET)
print(f"\nCleaned up bucket '{BUCKET}'")
