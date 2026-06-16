# SQL Window Functions

## What is this?

Regular SQL aggregations collapse rows. `GROUP BY` + `SUM()` turns 100 sales rows into one total. That's useful — but sometimes you want the total *alongside* each row, not instead of it.

**Window functions** perform calculations across a set of related rows while keeping each row intact. They "look through a window" at neighbouring rows to compute something — a running total, a rank, a comparison to the previous row — without collapsing the result.

```sql
-- Regular aggregation: collapses to one row
SELECT SUM(amount) FROM sales;
-- Result: 15000

-- Window function: keeps all rows, adds the total to each
SELECT name, amount, SUM(amount) OVER () AS total
FROM sales;
-- Result:
-- Alice  | 5000 | 15000
-- Bob    | 3000 | 15000
-- Carol  | 7000 | 15000
```

## What you can do with window functions

**Ranking** — rank products by sales within each category. `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`.

**Running totals** — cumulative sum of revenue over time. `SUM(...) OVER (ORDER BY date)`.

**Moving averages** — average of the last 7 days' sales. `AVG(...) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)`.

**Comparing to previous/next row** — how does today's revenue compare to yesterday's? `LAG()` and `LEAD()`.

**Percentiles** — which revenue percentile does each customer fall into? `NTILE()`, `PERCENT_RANK()`.

## Why not just do this in Python?

You could fetch all the data into Python and calculate running totals yourself. But the database can do this in a single pass over indexed data, often 10–100× faster than pulling all rows into memory and processing them in application code.

Window functions are especially powerful for dashboards, reports, and analytics queries.

## What the files cover

| File | What it teaches |
|---|---|
| `01_window_functions.py` | The `OVER` clause, `PARTITION BY`, `ORDER BY` within windows; ROW_NUMBER, RANK, LAG, LEAD, running totals, and moving averages |

## How to run

```bash
# Start the shared Postgres for all database-concepts modules (first run creates
# this module's database automatically). Skip if it's already running.
(cd .. && docker compose up -d)

pip install -r requirements.txt

python 01_window_functions.py
```
