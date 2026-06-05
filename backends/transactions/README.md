# Database Transactions

## What is this?

Imagine transferring $100 from your savings account to your checking account. That's two operations: subtract $100 from savings, add $100 to checking. What happens if the server crashes after the first step but before the second? The $100 has vanished.

A **transaction** is a group of database operations that the database treats as a single unit. Either all of them succeed, or none of them do. If anything goes wrong midway, the database automatically undoes everything back to the starting point. This "all or nothing" guarantee is called **atomicity**, and it's why your bank balance doesn't mysteriously disappear.

## ACID — the four guarantees

**Atomicity** — all operations in a transaction succeed or all are rolled back. No partial results.

**Consistency** — a transaction can only bring the database from one valid state to another. Rules and constraints are always enforced.

**Isolation** — concurrent transactions don't interfere with each other. Each transaction sees a consistent snapshot of the data.

**Durability** — once a transaction is committed, it stays committed. Even if the server crashes a millisecond later, the data is safe on disk.

## Isolation levels

Isolation is the trickiest guarantee. Full isolation (each transaction runs as if it's the only one) is expensive. Databases offer a spectrum of isolation levels with different trade-offs:

| Level | Prevents | Problem it allows |
|---|---|---|
| Read Uncommitted | nothing | Dirty reads (seeing uncommitted changes) |
| Read Committed | dirty reads | Non-repeatable reads |
| Repeatable Read | + non-repeatable reads | Phantom reads |
| Serializable | everything | Slowest — transactions run as if serial |

Most databases default to **Read Committed**. PostgreSQL defaults to **Read Committed** but behaves exceptionally well at **Repeatable Read**.

## What the files cover

| File | What it teaches |
|---|---|
| `01_acid.py` | Demonstrates each ACID property with concrete examples: what happens without them |
| `02_isolation.py` | Sets different isolation levels and shows the anomalies each one prevents |
| `03_savepoints.py` | Savepoints: partial rollbacks within a transaction — roll back part of the work without losing all of it |
| `04_locking.py` | How the database prevents two transactions from conflicting: row locks, table locks, deadlocks |

## How to run

```bash
# Requires PostgreSQL
docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres

python 01_acid.py
python 02_isolation.py
python 03_savepoints.py
python 04_locking.py
```
