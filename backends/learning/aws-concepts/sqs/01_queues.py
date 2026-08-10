import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client

sqs = client("sqs")

# --- Standard queue ---
print("=== Creating a standard queue ===")
resp = sqs.create_queue(
    QueueName="jobs",
    Attributes={
        "VisibilityTimeout": "30",       # seconds a message is hidden after receive
        "MessageRetentionPeriod": "86400", # keep messages for 1 day
        "ReceiveMessageWaitTimeSeconds": "20",  # long polling
    },
)
jobs_url = resp["QueueUrl"]
print(f"Created: {jobs_url}")

# --- FIFO queue ---
# FIFO queues guarantee order and exactly-once processing within a message group.
# They require the .fifo suffix and a MessageGroupId on every message.
print("\n=== Creating a FIFO queue ===")
resp = sqs.create_queue(
    QueueName="payments.fifo",
    Attributes={
        "FifoQueue": "true",
        "ContentBasedDeduplication": "true",  # auto-dedup using a hash of the body
    },
)
payments_url = resp["QueueUrl"]
print(f"Created: {payments_url}")

# --- List queues ---
print("\n=== Listing queues ===")
for url in sqs.list_queues().get("QueueUrls", []):
    print(f"  {url}")

# --- Read attributes ---
print("\n=== Queue attributes for 'jobs' ===")
attrs = sqs.get_queue_attributes(
    QueueUrl=jobs_url,
    AttributeNames=["All"],
)["Attributes"]
for key in ("VisibilityTimeout", "MessageRetentionPeriod", "ApproximateNumberOfMessages"):
    print(f"  {key}: {attrs.get(key)}")

# --- Cleanup ---
sqs.delete_queue(QueueUrl=jobs_url)
sqs.delete_queue(QueueUrl=payments_url)
print("\nDeleted both queues")
