import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client

sqs = client("sqs")
url = sqs.create_queue(QueueName="demo", Attributes={"VisibilityTimeout": "5"})["QueueUrl"]

# --- Send messages ---
print("=== Sending messages ===")
sqs.send_message(QueueUrl=url, MessageBody=json.dumps({"job": "resize_image", "id": 1}))
sqs.send_message(QueueUrl=url, MessageBody=json.dumps({"job": "send_email",   "id": 2}))
sqs.send_message(QueueUrl=url, MessageBody=json.dumps({"job": "resize_image", "id": 3}))

# Send with message attributes (metadata separate from the body)
sqs.send_message(
    QueueUrl=url,
    MessageBody=json.dumps({"job": "generate_report", "id": 4}),
    MessageAttributes={
        "priority": {"DataType": "String", "StringValue": "high"},
        "retry_count": {"DataType": "Number", "StringValue": "0"},
    },
)
print("Sent 4 messages")

# --- Batch send (up to 10 messages per call) ---
print("\n=== Batch send ===")
sqs.send_message_batch(
    QueueUrl=url,
    Entries=[
        {"Id": str(i), "MessageBody": json.dumps({"job": "task", "id": 10 + i})}
        for i in range(3)
    ],
)
print("Batch sent 3 more messages")

# --- Receive messages ---
# MaxNumberOfMessages: up to 10 per call. WaitTimeSeconds: long poll (waits up to N sec).
print("\n=== Receiving messages ===")
received = sqs.receive_message(
    QueueUrl=url,
    MaxNumberOfMessages=5,
    WaitTimeSeconds=1,
    MessageAttributeNames=["All"],
)["Messages"]

print(f"Received {len(received)} messages:")
for msg in received:
    body = json.loads(msg["Body"])
    attrs = msg.get("MessageAttributes", {})
    print(f"  [{body['id']}] {body['job']}  attrs={list(attrs.keys())}")

# Each received message is now invisible to other consumers (VisibilityTimeout=5s).
# You must delete it after successful processing, or it reappears.
print("\n=== Deleting processed messages ===")
for msg in received:
    sqs.delete_message(QueueUrl=url, ReceiptHandle=msg["ReceiptHandle"])
print(f"Deleted {len(received)} messages")

# --- Visibility timeout demo ---
# Receive a message, don't delete it, wait for the timeout, then receive again.
print("\n=== Visibility timeout demo ===")
msg = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=1, WaitTimeSeconds=1)["Messages"][0]
body = json.loads(msg["Body"])
print(f"Received: {body} — NOT deleting it, simulating a crash...")

# With VisibilityTimeout=5s, message reappears after 5 seconds
time.sleep(6)
retry = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=1, WaitTimeSeconds=1).get("Messages", [])
if retry:
    print(f"Message reappeared for retry: {json.loads(retry[0]['Body'])}")
    sqs.delete_message(QueueUrl=url, ReceiptHandle=retry[0]["ReceiptHandle"])

# --- Cleanup ---
remaining = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=10, WaitTimeSeconds=1).get("Messages", [])
for msg in remaining:
    sqs.delete_message(QueueUrl=url, ReceiptHandle=msg["ReceiptHandle"])
sqs.delete_queue(QueueUrl=url)
print("\nCleaned up queue")
