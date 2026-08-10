import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client

sns = client("sns")

# --- Create topics ---
print("=== Creating topics ===")
orders_arn = sns.create_topic(Name="order-events")["TopicArn"]
alerts_arn  = sns.create_topic(Name="system-alerts")["TopicArn"]
print(f"order-events ARN: {orders_arn}")
print(f"system-alerts ARN: {alerts_arn}")

# --- List topics ---
print("\n=== Listing topics ===")
for topic in sns.list_topics()["Topics"]:
    print(f"  {topic['TopicArn']}")

# --- Get topic attributes ---
print("\n=== Topic attributes ===")
attrs = sns.get_topic_attributes(TopicArn=orders_arn)["Attributes"]
for key in ("TopicArn", "DisplayName", "SubscriptionsConfirmed", "SubscriptionsPending"):
    print(f"  {key}: {attrs.get(key, '—')}")

# --- Set display name ---
sns.set_topic_attributes(TopicArn=orders_arn, AttributeName="DisplayName", AttributeValue="Order Events")
updated = sns.get_topic_attributes(TopicArn=orders_arn)["Attributes"]["DisplayName"]
print(f"\nDisplayName updated to: '{updated}'")

# --- Delete ---
print("\n=== Deleting topics ===")
sns.delete_topic(TopicArn=orders_arn)
sns.delete_topic(TopicArn=alerts_arn)
remaining = sns.list_topics()["Topics"]
print(f"Remaining topics: {len(remaining)}")
