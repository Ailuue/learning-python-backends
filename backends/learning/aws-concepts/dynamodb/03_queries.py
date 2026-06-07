import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client
from boto3.dynamodb.conditions import Key, Attr

db = client("dynamodb")
resource_db = __import__("helpers", fromlist=["resource"]).resource("dynamodb")
TABLE = "events"

# Setup: table with user_id (PK) + timestamp (SK)
db.create_table(
    TableName=TABLE,
    KeySchema=[
        {"AttributeName": "user_id", "KeyType": "HASH"},
        {"AttributeName": "timestamp", "KeyType": "RANGE"},
    ],
    AttributeDefinitions=[
        {"AttributeName": "user_id", "AttributeType": "S"},
        {"AttributeName": "timestamp", "AttributeType": "S"},
    ],
    BillingMode="PAY_PER_REQUEST",
)

table = resource_db.Table(TABLE)

# Seed data
items = [
    {"user_id": "u1", "timestamp": "2024-01-01T10:00:00", "event": "login",   "device": "mobile"},
    {"user_id": "u1", "timestamp": "2024-01-01T10:05:00", "event": "purchase","amount": 49},
    {"user_id": "u1", "timestamp": "2024-01-02T08:00:00", "event": "login",   "device": "desktop"},
    {"user_id": "u1", "timestamp": "2024-01-03T09:00:00", "event": "logout",  "device": "desktop"},
    {"user_id": "u2", "timestamp": "2024-01-01T11:00:00", "event": "login",   "device": "mobile"},
    {"user_id": "u2", "timestamp": "2024-01-01T11:30:00", "event": "purchase","amount": 120},
]
with table.batch_writer() as batch:
    for item in items:
        batch.put_item(Item=item)
print(f"Seeded {len(items)} items\n")

# --- Query by partition key only ---
# Fetches all events for u1. Fast — touches only u1's partition.
print("=== Query: all events for u1 ===")
result = table.query(KeyConditionExpression=Key("user_id").eq("u1"))
for item in result["Items"]:
    print(f"  {item['timestamp']}  {item['event']}")

# --- Query by PK + SK range ---
print("\n=== Query: u1 events on 2024-01-01 ===")
result = table.query(
    KeyConditionExpression=Key("user_id").eq("u1") & Key("timestamp").begins_with("2024-01-01"),
)
for item in result["Items"]:
    print(f"  {item['timestamp']}  {item['event']}")

# --- Query with FilterExpression ---
# Filter applies AFTER DynamoDB fetches the items for the partition — it doesn't reduce RCUs.
print("\n=== Query: u1 events, filter to purchases only ===")
result = table.query(
    KeyConditionExpression=Key("user_id").eq("u1"),
    FilterExpression=Attr("event").eq("purchase"),
)
for item in result["Items"]:
    print(f"  {item['timestamp']}  amount={item.get('amount')}")

# --- Scan (reads entire table) ---
# Avoid on large tables — reads every item regardless of key.
# Fine for small tables, admin scripts, or analytics on small datasets.
print("\n=== Scan: all purchases across all users ===")
result = table.scan(FilterExpression=Attr("event").eq("purchase"))
for item in result["Items"]:
    print(f"  user={item['user_id']}  ts={item['timestamp']}  amount={item.get('amount')}")

# --- Scan with projection (only fetch specific attributes) ---
print("\n=== Scan with projection (user_id + event only) ===")
result = table.scan(ProjectionExpression="user_id, #e", ExpressionAttributeNames={"#e": "event"})
for item in result["Items"]:
    print(f"  {item}")

# --- Cleanup ---
db.delete_table(TableName=TABLE)
print(f"\nCleaned up table '{TABLE}'")
