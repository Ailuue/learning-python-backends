# The N+1 Query Problem

## What is this?

The N+1 problem is one of the most common performance bugs in backend development. It's sneaky — the code looks correct, tests pass, and it works fine during development with a handful of rows. Then it hits production with 10,000 rows and the page takes 30 seconds to load.

Here's the pattern that causes it:

```python
# Fetch all 100 orders — that's 1 query
orders = session.query(Order).all()

# For each order, fetch the customer — that's N more queries
for order in orders:
    print(order.customer.name)   # triggers a query each time!
```

For 100 orders, this runs **101 queries** instead of 1. For 1,000 orders, it's 1,001 queries. The number of queries grows linearly with the number of rows — hence "N+1."

## Why does this happen?

ORMs like SQLAlchemy are helpful: when you access `order.customer`, they automatically run a query to fetch the related customer. This is called **lazy loading** — the relationship is loaded on demand. It's convenient but dangerous in loops.

## The fix: eager loading

Instead of loading relationships lazily (one at a time, as you access them), you load them eagerly (all at once, in the initial query):

```python
# Fetch orders AND their customers in a single query (JOIN)
orders = session.query(Order).options(joinedload(Order.customer)).all()

# Now order.customer is already loaded — no extra queries
for order in orders:
    print(order.customer.name)   # no query!
```

## What the files cover

| File | What it teaches |
|---|---|
| `01_n_plus_one.py` | Demonstrates the problem clearly — shows the query count growing with row count |
| `02_solutions.py` | The fixes: `joinedload` (SQL JOIN), `selectinload` (separate IN query), and when to use each |
| `03_tradeoffs.py` | Eager loading isn't always better — loading too much data has its own costs |

## How to run

```bash
# Start the shared Postgres for all database-concepts modules (first run creates
# this module's database automatically). Skip if it's already running.
(cd .. && docker compose up -d)

pip install -r requirements.txt

python 01_n_plus_one.py
python 02_solutions.py
python 03_tradeoffs.py
```
