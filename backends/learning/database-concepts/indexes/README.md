# Database Indexes

## What is this?

Imagine a 1,000-page book with no table of contents. Finding every mention of "PostgreSQL" means reading every single page. Now imagine the same book with an index at the back — "PostgreSQL: pages 4, 17, 203…" — and you jump straight there.

A **database index** works the same way. Without an index, a query like `WHERE email = 'alice@example.com'` requires the database to scan every row in the table. With an index on the `email` column, it jumps directly to the matching row in milliseconds, even in a table with 100 million rows.

Indexes are one of the highest-leverage performance tools in a backend developer's toolkit. A single index can turn a query that times out into one that responds in 1ms.

## The trade-off

Indexes make **reads faster** but **writes slightly slower**. Every time you insert, update, or delete a row, the database must also update all indexes on that table. For read-heavy workloads (most web apps), this trade-off is almost always worth it.

Indexes also use disk space. A large table with many indexes can use more disk for its indexes than for its actual data.

## Types of indexes

**B-tree** (default) — great for equality and range queries (`=`, `<`, `>`, `BETWEEN`, `ORDER BY`). The right choice 90% of the time.

**Hash** — only for equality (`=`). Slightly faster than B-tree for exact lookups, but less flexible.

**GIN (Generalized Inverted Index)** — for searching inside values: arrays, JSONB, and full-text search.

**GiST** — for geometric data, ranges, and full-text search. More flexible than GIN, slightly slower.

**Partial index** — an index that only covers rows matching a condition. E.g., index only active users: `WHERE deleted_at IS NULL`. Smaller and faster.

**Composite index** — an index on multiple columns. Column order matters: `(status, created_at)` helps queries filtering by `status` or by `status AND created_at`, but not queries filtering only by `created_at`.

## What the files cover

| File | What it teaches |
|---|---|
| `01_index_types.py` | Creating B-tree, partial, and composite indexes; demonstrating the speed difference with and without an index |
| `02_explain_analyze.py` | Using `EXPLAIN ANALYZE` to see the query plan — the database's step-by-step plan for answering your query, and whether it's using your index |

## How to run

```bash
# Requires PostgreSQL
docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres

python 01_index_types.py
python 02_explain_analyze.py
```
