import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client

s3 = client("s3")
BUCKET = "presigned-demo"
s3.create_bucket(Bucket=BUCKET)
s3.put_object(Bucket=BUCKET, Key="report.pdf", Body=b"(fake PDF content)")

# --- GET presigned URL ---
# Anyone with this URL can download the object for the duration — no AWS credentials needed.
# Use case: send a temporary download link to a user for their invoice/export/file.
print("=== Presigned GET URL ===")
url = s3.generate_presigned_url(
    "get_object",
    Params={"Bucket": BUCKET, "Key": "report.pdf"},
    ExpiresIn=3600,
)
print(f"Download URL (1hr expiry):\n  {url}\n")
print("Test it:  curl '<url>' -o report.pdf")

# --- PUT presigned URL ---
# The server generates this URL and hands it to the client. The client uploads directly
# to S3 without the file ever touching your server — saves bandwidth and compute.
# Use case: user avatar uploads, CSV imports, large file uploads from the browser.
print("\n=== Presigned PUT URL ===")
url = s3.generate_presigned_url(
    "put_object",
    Params={"Bucket": BUCKET, "Key": "user-upload.jpg", "ContentType": "image/jpeg"},
    ExpiresIn=300,
)
print(f"Upload URL (5min expiry):\n  {url}\n")
print("Test it:  curl -X PUT -H 'Content-Type: image/jpeg' --data-binary @photo.jpg '<url>'")

# --- POST presigned URL (browser form upload) ---
# PUT presigned URLs are simpler but require setting headers, which browser forms can't do.
# generate_presigned_post returns a URL + a fields dict you put in the HTML <form>.
# You can also add Conditions to enforce file size limits and content type on the S3 side.
print("\n=== Presigned POST (HTML form upload) ===")
response = s3.generate_presigned_post(
    BUCKET,
    "avatars/${filename}",
    Fields={"Content-Type": "image/png"},
    Conditions=[
        {"Content-Type": "image/png"},
        ["content-length-range", 1, 5_000_000],
    ],
    ExpiresIn=600,
)
print(f"POST to:     {response['url']}")
print(f"Form fields: {list(response['fields'].keys())}")
print("\nIn the browser form, include all fields[] as hidden inputs, then the file last.")

# --- Cleanup ---
s3.delete_object(Bucket=BUCKET, Key="report.pdf")
s3.delete_bucket(Bucket=BUCKET)
print("\nCleaned up.")
