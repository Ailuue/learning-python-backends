import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client

s3 = client("s3")

# --- Create ---
print("=== Creating buckets ===")
s3.create_bucket(Bucket="my-app-uploads")
s3.create_bucket(Bucket="my-app-backups")
print("Created: my-app-uploads, my-app-backups")

# --- List ---
print("\n=== Listing buckets ===")
response = s3.list_buckets()
for b in response["Buckets"]:
    print(f"  {b['Name']}  (created: {b['CreationDate'].date()})")

# --- Tag ---
print("\n=== Tagging a bucket ===")
s3.put_bucket_tagging(
    Bucket="my-app-uploads",
    Tagging={"TagSet": [{"Key": "env", "Value": "dev"}, {"Key": "team", "Value": "backend"}]},
)
tags = s3.get_bucket_tagging(Bucket="my-app-uploads")["TagSet"]
print(f"Tags on my-app-uploads: {tags}")

# --- Versioning ---
print("\n=== Enabling versioning ===")
s3.put_bucket_versioning(
    Bucket="my-app-uploads",
    VersioningConfiguration={"Status": "Enabled"},
)
status = s3.get_bucket_versioning(Bucket="my-app-uploads").get("Status", "Disabled")
print(f"Versioning on my-app-uploads: {status}")
# With versioning on, deleting an object adds a delete marker instead of removing it.
# You can restore previous versions, which is key for audit trails and accidental deletion recovery.

# --- Delete ---
print("\n=== Deleting buckets ===")
# Buckets must be empty before deletion (versioning means you'd also need to delete versions)
s3.delete_bucket(Bucket="my-app-uploads")
s3.delete_bucket(Bucket="my-app-backups")
print("Deleted both buckets")

remaining = [b["Name"] for b in s3.list_buckets()["Buckets"]]
print(f"Remaining buckets: {remaining}")
