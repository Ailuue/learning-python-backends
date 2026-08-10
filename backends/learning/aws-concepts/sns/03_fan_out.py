import sys
import os
import json
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client

sns = client("sns")
sqs = client("sqs")

# Fan-out pattern: "order.placed" event → billing queue AND inventory queue, simultaneously.
# Each service gets its own queue and processes independently — total decoupling.
print("=== Fan-out: SNS topic → 2 SQS queues ===\n")

# --- Infrastructure ---
topic_arn = sns.create_topic(Name="order-events")["TopicArn"]

billing_url   = sqs.create_queue(QueueName="billing-queue")["QueueUrl"]
inventory_url = sqs.create_queue(QueueName="inventory-queue")["QueueUrl"]
alerts_url    = sqs.create_queue(QueueName="alerts-queue")["QueueUrl"]

def get_arn(url):
    return sqs.get_queue_attributes(QueueUrl=url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]

billing_arn   = get_arn(billing_url)
inventory_arn = get_arn(inventory_url)
alerts_arn    = get_arn(alerts_url)

def allow_sns(queue_url, queue_arn, topic_arn):
    sqs.set_queue_attributes(
        QueueUrl=queue_url,
        Attributes={"Policy": json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Principal": "*", "Action": "sqs:SendMessage",
                           "Resource": queue_arn, "Condition": {"ArnEquals": {"aws:SourceArn": topic_arn}}}],
        })},
    )

allow_sns(billing_url, billing_arn, topic_arn)
allow_sns(inventory_url, inventory_arn, topic_arn)
allow_sns(alerts_url, alerts_arn, topic_arn)

# --- Subscribe all 3 queues ---
# billing and inventory: receive ALL order events
# alerts: only receive high-value orders (amount > threshold, handled via filter policy)
sns.subscribe(TopicArn=topic_arn, Protocol="sqs", Endpoint=billing_arn)
sns.subscribe(TopicArn=topic_arn, Protocol="sqs", Endpoint=inventory_arn)

# Filter policy: alerts queue only receives messages where event_type = "order.placed" AND amount >= 100
alerts_sub = sns.subscribe(
    TopicArn=topic_arn,
    Protocol="sqs",
    Endpoint=alerts_arn,
    Attributes={"FilterPolicy": json.dumps({
        "event_type": ["order.placed"],
        "high_value":  ["true"],
    })},
)
print("Subscribed billing, inventory (all orders) and alerts (high-value orders only)")

# --- Publish events ---
print("\n=== Publishing order events ===")

# Small order — should reach billing + inventory, but NOT alerts
sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps({"order_id": "ord-001", "total": 19.99}),
    MessageAttributes={
        "event_type": {"DataType": "String", "StringValue": "order.placed"},
        "high_value":  {"DataType": "String", "StringValue": "false"},
    },
)
print("Published: ord-001 ($19.99) — small order")

# Large order — should reach all 3 queues
sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps({"order_id": "ord-002", "total": 499.00}),
    MessageAttributes={
        "event_type": {"DataType": "String", "StringValue": "order.placed"},
        "high_value":  {"DataType": "String", "StringValue": "true"},
    },
)
print("Published: ord-002 ($499.00) — high-value order")

time.sleep(1)

# --- Inspect each queue ---
def drain(url, name):
    msgs = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=10, WaitTimeSeconds=2).get("Messages", [])
    orders = [json.loads(json.loads(m["Body"])["Message"])["order_id"] for m in msgs]
    print(f"  {name}: {orders}")

print("\n=== Messages received per queue ===")
drain(billing_url,   "billing  ")
drain(inventory_url, "inventory")
drain(alerts_url,    "alerts   ")
# Expected:
#   billing:   [ord-001, ord-002]
#   inventory: [ord-001, ord-002]
#   alerts:    [ord-002]  ← filter policy excluded ord-001

# --- Cleanup ---
sns.delete_topic(TopicArn=topic_arn)
for url in [billing_url, inventory_url, alerts_url]:
    sqs.delete_queue(QueueUrl=url)
print("\nCleaned up.")
