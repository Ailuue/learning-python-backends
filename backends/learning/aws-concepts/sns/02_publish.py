import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client

sns = client("sns")
sqs = client("sqs")

# Setup: topic + one SQS subscriber so we can inspect what arrived
topic_arn = sns.create_topic(Name="events")["TopicArn"]
queue_url  = sqs.create_queue(QueueName="events-inbox")["QueueUrl"]
queue_arn  = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]

# Allow SNS to write to the SQS queue
sqs.set_queue_attributes(
    QueueUrl=queue_url,
    Attributes={"Policy": json.dumps({
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Principal": "*", "Action": "sqs:SendMessage",
                       "Resource": queue_arn, "Condition": {"ArnEquals": {"aws:SourceArn": topic_arn}}}],
    })},
)
sns.subscribe(TopicArn=topic_arn, Protocol="sqs", Endpoint=queue_arn)

# --- Basic publish ---
print("=== Basic publish ===")
resp = sns.publish(TopicArn=topic_arn, Message="Hello from SNS!")
print(f"MessageId: {resp['MessageId']}")

# --- Publish with Subject and MessageAttributes ---
# MessageAttributes let subscribers filter messages without inspecting the body.
print("\n=== Publish with attributes ===")
resp = sns.publish(
    TopicArn=topic_arn,
    Subject="Order Placed",
    Message=json.dumps({"order_id": "ord-999", "total": 79.99, "user_id": "u1"}),
    MessageAttributes={
        "event_type": {"DataType": "String", "StringValue": "order.placed"},
        "region":     {"DataType": "String", "StringValue": "eu-west-1"},
        "amount":     {"DataType": "Number", "StringValue": "79.99"},
    },
)
print(f"Published order event: {resp['MessageId']}")

# --- Read from the SQS queue to see what arrived ---
import time; time.sleep(1)
print("\n=== Messages received in SQS ===")
messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=2).get("Messages", [])
for msg in messages:
    # SNS wraps the message in an envelope — the actual body is in the 'Message' field
    envelope = json.loads(msg["Body"])
    print(f"  Type:    {envelope.get('Type')}")
    print(f"  Subject: {envelope.get('Subject', '—')}")
    print(f"  Message: {envelope.get('Message')}")
    print()

# --- Cleanup ---
sns.delete_topic(TopicArn=topic_arn)
sqs.delete_queue(QueueUrl=queue_url)
print("Cleaned up.")
