import sys
import os
import json
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client

sqs = client("sqs")

# --- Create a DLQ ---
# The DLQ is just a normal queue. You wire it to a source queue via a redrive policy.
print("=== Creating DLQ + source queue ===")
dlq_url = sqs.create_queue(QueueName="jobs-dlq")["QueueUrl"]
dlq_arn = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
print(f"DLQ ARN: {dlq_arn}")

# maxReceiveCount=2: after 2 failed receives (message becomes visible again twice), move to DLQ
source_url = sqs.create_queue(
    QueueName="jobs",
    Attributes={
        "VisibilityTimeout": "2",
        "RedrivePolicy": json.dumps({
            "deadLetterTargetArn": dlq_arn,
            "maxReceiveCount": "2",
        }),
    },
)["QueueUrl"]
print("Source queue with redrive policy created")

# --- Seed a "poison pill" message that always fails ---
sqs.send_message(QueueUrl=source_url, MessageBody=json.dumps({"job": "bad_job", "will_fail": True}))
sqs.send_message(QueueUrl=source_url, MessageBody=json.dumps({"job": "good_job", "will_fail": False}))
print("\nSent 1 poison-pill + 1 good message")

def process(msg: dict) -> bool:
    return not msg.get("will_fail", False)

# --- Simulate processing with failures ---
# Each time a consumer receives a message and doesn't delete it, the receive count increments.
# After maxReceiveCount receives, SQS automatically moves it to the DLQ.
print("\n=== Processing loop (simulating 3 rounds) ===")
for round_num in range(1, 4):
    print(f"\n--- Round {round_num} ---")
    time.sleep(2)  # wait for visibility timeout to expire
    messages = sqs.receive_message(
        QueueUrl=source_url, MaxNumberOfMessages=10, WaitTimeSeconds=1,
        AttributeNames=["ApproximateReceiveCount"],
    ).get("Messages", [])

    if not messages:
        print("  No messages available")
        continue

    for msg in messages:
        body = json.loads(msg["Body"])
        receive_count = int(msg["Attributes"]["ApproximateReceiveCount"])
        success = process(body)
        print(f"  job={body['job']}  receive_count={receive_count}  success={success}")
        if success:
            sqs.delete_message(QueueUrl=source_url, ReceiptHandle=msg["ReceiptHandle"])
            print("    → Deleted (processed successfully)")
        else:
            print(f"    → NOT deleted (will retry or go to DLQ after {2 - receive_count} more failures)")

# --- Inspect the DLQ ---
print("\n=== Inspecting DLQ ===")
time.sleep(3)
dlq_msgs = sqs.receive_message(QueueUrl=dlq_url, MaxNumberOfMessages=10, WaitTimeSeconds=2).get("Messages", [])
print(f"Messages in DLQ: {len(dlq_msgs)}")
for msg in dlq_msgs:
    print(f"  {json.loads(msg['Body'])}")

# In production you'd inspect the DLQ, fix the bug, then redrive messages back to the source queue.

# --- Cleanup ---
sqs.delete_queue(QueueUrl=source_url)
sqs.delete_queue(QueueUrl=dlq_url)
print("\nCleaned up queues")
