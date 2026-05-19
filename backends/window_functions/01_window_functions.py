"""
Window Functions
================
A window function computes a value for each row using a *window* — a set of
rows related to the current row — WITHOUT collapsing those rows the way
GROUP BY does. Every row in the result stays intact; it just gains an extra
computed column derived from its neighbours.

Syntax:
  function_name(...) OVER (
      [PARTITION BY col, ...]   -- divide rows into independent groups
      [ORDER BY col, ...]       -- order within each partition
      [ROWS/RANGE BETWEEN ...]  -- explicit frame (optional)
  )

The OVER clause is what makes something a window function. Any ordinary
aggregate (SUM, AVG, COUNT, MAX, MIN) can be used as a window function;
PostgreSQL also provides window-only functions like ROW_NUMBER and LAG.

Ranking functions:
  ROW_NUMBER()    — always unique: 1, 2, 3, 4, ...  (ties broken arbitrarily)
  RANK()          — ties share a rank, next rank skips:  1, 2, 2, 4
  DENSE_RANK()    — ties share a rank, no skipping:      1, 2, 2, 3

Offset functions:
  LAG(col, n)     — value from n rows *before* the current row in the window
  LEAD(col, n)    — value from n rows *after* the current row in the window
  Both return NULL at the boundary unless you supply a default third argument.

Running / cumulative aggregates:
  SUM(col) OVER (ORDER BY date)
  When ORDER BY is present the default frame is
  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW — i.e. "everything so far".
  That's what produces a running total.

Partitioned aggregates (no ORDER BY):
  AVG(col) OVER (PARTITION BY category)
  When there is no ORDER BY the default frame is the entire partition, so every
  row in the partition sees the same aggregate value. Unlike GROUP BY, the rows
  are NOT merged — each sale row keeps its own amount AND sees the group avg.

Key gotcha — you cannot reference a window function in WHERE directly:
  -- WRONG:
  SELECT *, ROW_NUMBER() OVER (...) AS rn FROM t WHERE rn = 1;
  -- RIGHT: wrap in a subquery or CTE, then filter:
  WITH ranked AS (SELECT *, ROW_NUMBER() OVER (...) AS rn FROM t)
  SELECT * FROM ranked WHERE rn = 1;

Demo scenario:
  wf_sales — rep, category, amount, sale_date
  15 rows of sales data across four reps and three categories.
  Some amounts are intentionally tied to make RANK vs DENSE_RANK visible:
    Electronics: Alice and Bob both 1200  →  rank 1, 1, 3 vs dense 1, 1, 2
    Clothing:    Bob and Carol both 550   →  same pattern
    Books:       Alice and Carol both 200 →  same pattern
"""

import db


SETUP = """
DROP TABLE IF EXISTS wf_sales;

CREATE TABLE wf_sales (
    sale_id   SERIAL PRIMARY KEY,
    rep       TEXT   NOT NULL,
    category  TEXT   NOT NULL,
    amount    INT    NOT NULL,
    sale_date DATE   NOT NULL
);
"""

SEED = """
INSERT INTO wf_sales (rep, category, amount, sale_date) VALUES
    ('Alice', 'Electronics', 1200, '2026-01-05'),
    ('Bob',   'Electronics', 1200, '2026-01-12'),
    ('Carol', 'Electronics',  900, '2026-01-18'),
    ('David', 'Electronics',  750, '2026-01-22'),
    ('Alice', 'Clothing',     400, '2026-02-03'),
    ('Bob',   'Clothing',     550, '2026-02-08'),
    ('Carol', 'Clothing',     550, '2026-02-14'),
    ('David', 'Clothing',     300, '2026-02-19'),
    ('Alice', 'Books',        200, '2026-03-02'),
    ('Bob',   'Books',        150, '2026-03-09'),
    ('Carol', 'Books',        200, '2026-03-15'),
    ('David', 'Books',        350, '2026-03-20'),
    ('Alice', 'Electronics',  950, '2026-04-01'),
    ('Bob',   'Clothing',     480, '2026-04-10'),
    ('Carol', 'Books',        180, '2026-04-17');
"""


def demo_ranking(cur):
    print("=" * 68)
    print("RANKING FUNCTIONS  —  ROW_NUMBER / RANK / DENSE_RANK")
    print("=" * 68)
    print(
        "All three rank rows within each category by amount DESC.\n"
        "Electronics: Alice and Bob both sold 1200.\n"
        "  RANK      → 1, 1, 3   (skips 2)\n"
        "  DENSE_RANK → 1, 1, 2   (no skip)\n"
        "  ROW_NUMBER → 1, 2, 3   (always unique — tie broken by insertion order)\n"
    )
    db.print_table(
        cur,
        """
        SELECT
            category,
            rep,
            amount,
            ROW_NUMBER() OVER (PARTITION BY category ORDER BY amount DESC) AS row_num,
            RANK()       OVER (PARTITION BY category ORDER BY amount DESC) AS rank,
            DENSE_RANK() OVER (PARTITION BY category ORDER BY amount DESC) AS dense_rank
        FROM   wf_sales
        ORDER  BY category, amount DESC, rep
        """,
        ["category", "rep", "amount", "row_num", "rank", "dense_rank"],
    )


def demo_running_total(cur):
    print("=" * 68)
    print("RUNNING TOTAL  —  SUM() OVER (PARTITION BY rep ORDER BY sale_date)")
    print("=" * 68)
    print(
        "ORDER BY inside OVER activates the default frame:\n"
        "  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW\n"
        "so each row's running_total is the sum of all rows up to and\n"
        "including the current one. PARTITION BY rep resets it per rep.\n"
    )
    db.print_table(
        cur,
        """
        SELECT
            rep,
            sale_date,
            category,
            amount,
            SUM(amount) OVER (
                PARTITION BY rep
                ORDER BY     sale_date
            ) AS running_total
        FROM   wf_sales
        ORDER  BY rep, sale_date
        """,
        ["rep", "sale_date", "category", "amount", "running_total"],
    )


def demo_lag(cur):
    print("=" * 68)
    print("LAG  —  comparing each sale to the same rep's previous sale")
    print("=" * 68)
    print(
        "LAG(amount, 1) returns the amount from the row immediately before\n"
        "this one in the partition's ordering. First row per rep → NULL.\n"
        "Wrapping in a subquery lets us reference prev_amount in the outer\n"
        "SELECT without repeating the whole window expression.\n"
    )
    db.print_table(
        cur,
        """
        SELECT
            rep,
            sale_date,
            amount,
            prev_amount,
            amount - prev_amount AS change
        FROM (
            SELECT
                rep,
                sale_date,
                amount,
                LAG(amount, 1) OVER (
                    PARTITION BY rep
                    ORDER BY     sale_date
                ) AS prev_amount
            FROM wf_sales
        ) t
        ORDER BY rep, sale_date
        """,
        ["rep", "sale_date", "amount", "prev_amount", "change"],
    )


def demo_partition_avg(cur):
    print("=" * 68)
    print("PARTITIONED AGGREGATE  —  AVG() OVER (PARTITION BY category)")
    print("=" * 68)
    print(
        "No ORDER BY means the frame is the entire partition.\n"
        "Every row in the same category sees the same cat_avg.\n"
        "vs_avg shows whether this particular sale was above (+) or\n"
        "below (−) the category average — impossible with GROUP BY alone.\n"
    )
    db.print_table(
        cur,
        """
        SELECT
            category,
            rep,
            amount,
            ROUND(AVG(amount) OVER (PARTITION BY category)) AS cat_avg,
            amount - ROUND(AVG(amount) OVER (PARTITION BY category)) AS vs_avg
        FROM   wf_sales
        ORDER  BY category, amount DESC
        """,
        ["category", "rep", "amount", "cat_avg", "vs_avg"],
    )


def demo_top_per_group(cur):
    print("=" * 68)
    print("TOP N PER GROUP  —  ROW_NUMBER in a CTE, then filter")
    print("=" * 68)
    print(
        "Classic pattern: number rows within each partition, wrap in a CTE,\n"
        "then WHERE rn = 1. This is the cleanest way to get the best row\n"
        "per group — GROUP BY cannot do this without a messy subquery.\n"
        "Use RANK() instead of ROW_NUMBER() if you want tied leaders included.\n"
    )
    db.print_table(
        cur,
        """
        WITH ranked AS (
            SELECT
                category,
                rep,
                amount,
                ROW_NUMBER() OVER (
                    PARTITION BY category
                    ORDER BY     amount DESC
                ) AS rn
            FROM wf_sales
        )
        SELECT category, rep, amount
        FROM   ranked
        WHERE  rn = 1
        ORDER  BY category
        """,
        ["category", "rep", "amount"],
    )
    print(
        "ROW_NUMBER breaks ties arbitrarily (Alice and Bob both sold 1200\n"
        "in Electronics — only one is returned). Swap in RANK() and filter\n"
        "WHERE rn = 1 to return both tied leaders.\n"
    )


def main():
    with db.cursor() as cur:
        print("\nSetting up tables...")
        cur.execute(SETUP)
        cur.execute(SEED)
        print("Done.\n")

        demo_ranking(cur)
        demo_running_total(cur)
        demo_lag(cur)
        demo_partition_avg(cur)
        demo_top_per_group(cur)


if __name__ == "__main__":
    main()
