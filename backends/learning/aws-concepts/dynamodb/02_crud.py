import sys, os
from decimal import Decimal
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers import client

db = client("dynamodb")
TABLE = "products"

db.create_table(
    TableName=TABLE,
    KeySchema=[{"AttributeName": "product_id", "KeyType": "HASH"}],
    AttributeDefinitions=[{"AttributeName": "product_id", "AttributeType": "S"}],
    BillingMode="PAY_PER_REQUEST",
)

# --- PutItem (insert or fully replace) ---
print("=== PutItem ===")
db.put_item(
    TableName=TABLE,
    Item={
        "product_id": {"S": "prod-001"},
        "name": {"S": "Wireless Headphones"},
        "price": {"N": "79.99"},
        "stock": {"N": "150"},
        "tags": {"SS": ["electronics", "audio"]},
        "in_stock": {"BOOL": True},
    },
)
db.put_item(
    TableName=TABLE,
    Item={
        "product_id": {"S": "prod-002"},
        "name": {"S": "USB-C Cable"},
        "price": {"N": "12.99"},
        "stock": {"N": "500"},
        "in_stock": {"BOOL": True},
    },
)
print("Inserted prod-001 and prod-002")

# --- GetItem ---
print("\n=== GetItem ===")
item = db.get_item(
    TableName=TABLE,
    Key={"product_id": {"S": "prod-001"}},
)["Item"]
print(f"  name:  {item['name']['S']}")
print(f"  price: {item['price']['N']}")
print(f"  tags:  {item['tags']['SS']}")

# --- UpdateItem with expressions ---
# UpdateExpression lets you modify specific attributes without rewriting the whole item.
# SET adds/updates attributes, ADD increments numbers, REMOVE deletes attributes.
print("\n=== UpdateItem ===")
db.update_item(
    TableName=TABLE,
    Key={"product_id": {"S": "prod-001"}},
    UpdateExpression="SET price = :p, #n = :n ADD stock :delta",
    ExpressionAttributeValues={
        ":p": {"N": "69.99"},   # price drop
        ":n": {"S": "Wireless Headphones Pro"},
        ":delta": {"N": "-10"},  # sold 10 units
    },
    ExpressionAttributeNames={"#n": "name"},  # 'name' is a reserved word in DynamoDB
)
updated = db.get_item(TableName=TABLE, Key={"product_id": {"S": "prod-001"}})["Item"]
print(f"  new name:  {updated['name']['S']}")
print(f"  new price: {updated['price']['N']}")
print(f"  new stock: {updated['stock']['N']}")

# --- Conditional update (optimistic locking pattern) ---
# Only apply the update if the condition holds; raises ConditionalCheckFailedException otherwise.
print("\n=== Conditional UpdateItem ===")
try:
    db.update_item(
        TableName=TABLE,
        Key={"product_id": {"S": "prod-001"}},
        UpdateExpression="SET in_stock = :false",
        ConditionExpression="stock = :zero",
        ExpressionAttributeValues={":false": {"BOOL": False}, ":zero": {"N": "0"}},
    )
except db.exceptions.ConditionalCheckFailedException:
    print("  Condition failed: stock is not 0, in_stock not changed (correct)")

# --- DeleteItem ---
print("\n=== DeleteItem ===")
db.delete_item(TableName=TABLE, Key={"product_id": {"S": "prod-002"}})
print("  Deleted prod-002")

remaining = db.scan(TableName=TABLE)["Items"]
print(f"  Items remaining: {[i['product_id']['S'] for i in remaining]}")

# --- Cleanup ---
db.delete_table(TableName=TABLE)
print(f"\nCleaned up table '{TABLE}'")
