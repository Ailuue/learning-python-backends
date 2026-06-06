# Database Normalization

## What is this?

When you design a database table, the obvious first instinct is to put everything in one place:

| order_id | customer_name | customer_email | item | item_price | category |
|---|---|---|---|---|---|
| 1 | Alice | alice@example.com | Keyboard | 79.99 | Electronics |
| 2 | Alice | alice@example.com | Mouse | 29.99 | Electronics |
| 3 | Bob | bob@example.com | Desk | 299.99 | Furniture |

This seems fine — until Alice changes her email. Now you have to update every row that mentions her. Miss one, and your data is inconsistent: two rows disagree on Alice's email. This is called an **update anomaly**, and it's one of several ways that poorly structured data causes bugs.

**Normalization** is a process of organizing your data to eliminate these problems. You split data into separate tables and use foreign keys to connect them. Alice's email lives in one place — the `customers` table. Orders just reference her customer ID.

## The normal forms

Normalization is defined in levels called **normal forms** (1NF, 2NF, 3NF, BCNF). Each level fixes a different class of problem. In practice, most well-designed databases aim for 3NF.

**1NF** — each column holds one value (no lists or repeating groups in a cell).

**2NF** — every non-key column depends on the *whole* primary key, not just part of it. Relevant when you have composite primary keys.

**3NF** — every non-key column depends *directly* on the primary key, not on another non-key column. Eliminates transitive dependencies (e.g., storing both `zip_code` and `city` when city is determined by zip_code).

**BCNF** — a stricter version of 3NF that handles edge cases with overlapping candidate keys.

## When to break the rules

Normalization reduces redundancy but can require more JOINs to query data. For read-heavy workloads or analytics, **denormalization** (intentionally duplicating data) can improve query performance. This is a deliberate trade-off, not a mistake.

## What the files cover

| File | What it teaches |
|---|---|
| `01_unnormalized.py` | A flat table with all the problems: update anomalies, insertion anomalies, deletion anomalies |
| `02_1nf.py` | First Normal Form: atomic values, no repeating groups |
| `03_2nf.py` | Second Normal Form: eliminating partial dependencies |
| `04_3nf.py` | Third Normal Form: eliminating transitive dependencies |
| `05_bcnf.py` | Boyce-Codd Normal Form: the stricter final step |

## How to run

```bash
# Requires PostgreSQL
docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres

python 01_unnormalized.py
python 02_1nf.py
# ... and so on
```
