import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client

db = client("dynamodb")
TABLE = "orders"

# --- Create table with composite key ---
# PK = user_id, SK = order_id  →  "all orders for a user" is a natural query
print("=== Creating table ===")
db.create_table(
    TableName=TABLE,
    KeySchema=[
        {"AttributeName": "user_id", "KeyType": "HASH"},   # partition key
        {"AttributeName": "order_id", "KeyType": "RANGE"},  # sort key
    ],
    AttributeDefinitions=[
        {"AttributeName": "user_id", "AttributeType": "S"},
        {"AttributeName": "order_id", "AttributeType": "S"},
        {"AttributeName": "status", "AttributeType": "S"},  # needed for the GSI below
    ],
    # GSI: lets us query orders by status regardless of user_id
    GlobalSecondaryIndexes=[
        {
            "IndexName": "status-index",
            "KeySchema": [{"AttributeName": "status", "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "ALL"},
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        }
    ],
    BillingMode="PROVISIONED",
    ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
)
print(f"Table '{TABLE}' created")

# --- Describe ---
print("\n=== Describing table ===")
desc = db.describe_table(TableName=TABLE)["Table"]
print(f"  Status:      {desc['TableStatus']}")
print(f"  Item count:  {desc['ItemCount']}")
print(f"  Key schema:  {desc['KeySchema']}")
gsi_names = [g["IndexName"] for g in desc.get("GlobalSecondaryIndexes", [])]
print(f"  GSIs:        {gsi_names}")

# --- List all tables ---
print("\n=== Listing tables ===")
tables = db.list_tables()["TableNames"]
print(f"  {tables}")

# --- Cleanup ---
db.delete_table(TableName=TABLE)
print(f"\nDeleted table '{TABLE}'")
