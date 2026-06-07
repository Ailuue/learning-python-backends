# DynamoDB

DynamoDB is a fully managed NoSQL database. It stores items (like rows) in tables, addressed by a primary key.
Unlike a relational database, there is no fixed schema — each item can have different attributes.

## Key concepts

- **Table** — a collection of items. You provision it with a primary key schema upfront; nothing else is fixed.
- **Partition key (PK)** — required. DynamoDB hashes this to decide which partition stores the item.
- **Sort key (SK)** — optional. Combined with the PK to form a composite key. Enables range queries within a partition.
- **Item** — a collection of attributes (like a row). Only the key attributes are required.
- **GSI (Global Secondary Index)** — a secondary index with a *different* PK/SK, letting you query by non-key attributes efficiently.
- **Query** — fetch items by partition key (and optionally filter by sort key). Fast — targets one partition.
- **Scan** — read every item in the table, then optionally filter. Expensive — avoid on large tables.

## Access patterns drive the design

In DynamoDB you design the table *around the queries you need*, not the other way around.
If you need to look up orders by user AND by date, you model that into the keys or a GSI upfront.

## What the files cover

| File | What it teaches |
|------|----------------|
| `01_tables.py` | Create a table with composite key, add a GSI, describe the table |
| `02_crud.py` | PutItem, GetItem, UpdateItem (expressions), DeleteItem |
| `03_queries.py` | Query by PK, query by PK+SK range, Scan with FilterExpression |

## How to run

```bash
python dynamodb/01_tables.py
python dynamodb/02_crud.py
python dynamodb/03_queries.py
```
