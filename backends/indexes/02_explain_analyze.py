"""
EXPLAIN ANALYZE — Reading Query Plans
======================================
Every query in PostgreSQL goes through the query planner, which chooses
HOW to execute the query. EXPLAIN shows that plan. EXPLAIN ANALYZE runs
the query and adds actual timings and row counts alongside the estimates.

Reading a plan node:

  Seq Scan on exp_orders  (cost=0.00..1543.00 rows=50000 width=40)
                          (actual time=0.013..9.211 rows=50000 loops=1)
    Filter: (status = 'pending')
    Rows Removed by Filter: 37412

  cost=A..B    — planner estimate; A=startup (before first row), B=total.
                 Units are abstract — only compare nodes within the same plan.
  rows=N       — planner's ESTIMATED output rows (from table statistics)
  width=N      — estimated average row size in bytes
  actual time  — real milliseconds; multiply by loops for total node cost
  actual rows  — real rows this node returned
  loops=N      — times this node executed (common in joins/subqueries)
  Filter:      — condition checked AFTER row is fetched → wasted reads
  Index Cond:  — condition resolved BY the index → no wasted reads
  Rows Removed by Filter: — the higher this is, the more wasted work

Common node types:
  Seq Scan          — reads every row. Fine for small tables; bad otherwise.
  Index Scan        — uses index, fetches matching heap rows one by one.
  Index Only Scan   — answered entirely from the index (fastest).
  Bitmap Heap Scan  — two-phase: build bitmap from index, then batch-fetch pages.
  Hash Join         — hashes one side, probes with the other.
  Nested Loop       — for each outer row, look up inner via index.

Key question when reading a plan: are the estimated rows close to actual rows?
A big gap means stale statistics — run ANALYZE to fix.

Demo setup:
  exp_products (200 rows)  — small table; seq scan is expected and correct
  exp_orders  (50 000 rows) — large table; shows seq scan vs index scan contrast
"""

import db


SETUP = """
DROP TABLE IF EXISTS exp_orders;
DROP TABLE IF EXISTS exp_products;

CREATE TABLE exp_products (
    product_id   SERIAL PRIMARY KEY,
    name         TEXT   NOT NULL,
    category     TEXT   NOT NULL,
    price        NUMERIC(10, 2) NOT NULL
);

CREATE TABLE exp_orders (
    order_id   SERIAL  PRIMARY KEY,
    user_id    INT     NOT NULL,
    status     TEXT    NOT NULL,
    amount     NUMERIC(10, 2) NOT NULL,
    created_at DATE    NOT NULL
);
"""

SEED = """
INSERT INTO exp_products (name, category, price)
SELECT
    'Product ' || i,
    CASE (i % 4)
        WHEN 0 THEN 'electronics'
        WHEN 1 THEN 'clothing'
        WHEN 2 THEN 'food'
        ELSE        'books'
    END,
    (random() * 500 + 1)::NUMERIC(10, 2)
FROM generate_series(1, 200) i;

INSERT INTO exp_orders (user_id, status, amount, created_at)
SELECT
    (random() * 999 + 1)::INT,
    CASE (i % 10)
        WHEN 0 THEN 'cancelled'
        WHEN 1 THEN 'refunded'
        ELSE        'completed'     -- 80% of rows are 'completed'
    END,
    (random() * 1000 + 1)::NUMERIC(10, 2),
    '2025-01-01'::DATE + (random() * 364)::INT
FROM generate_series(1, 50000) i;

ANALYZE exp_products;
ANALYZE exp_orders;
"""


def explain(cur, label, query, params=None):
    """Run EXPLAIN ANALYZE and print the raw plan with a label."""
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"{'─' * 60}")
    cur.execute(f"EXPLAIN (ANALYZE, BUFFERS) {query}", params)
    for row in cur.fetchall():
        print(row[0])
    print()


def section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def main():
    with db.cursor() as cur:
        cur.execute(SETUP)
        cur.execute(SEED)

        # ── 1. Seq Scan on a small table ─────────────────────────────────
        section("1. SEQ SCAN — small table (expected, correct)")
        print(
            "exp_products has 200 rows. PostgreSQL will choose a Seq Scan\n"
            "even if an index exists — it's cheaper than an index lookup\n"
            "for a table this small.\n"
        )
        cur.execute("CREATE INDEX exp_idx_product_category ON exp_products(category)")
        explain(
            cur,
            "WHERE category = 'electronics'  on 200-row table",
            "SELECT * FROM exp_products WHERE category = 'electronics'",
        )
        print(
            "WHAT TO LOOK FOR:\n"
            "  • Node type is 'Seq Scan' — reads every row.\n"
            "  • The index exists but was ignored. This is CORRECT.\n"
            "  • 200 rows is well below the threshold where index overhead pays off.\n"
            "  • 'Rows Removed by Filter' shows rows fetched but discarded.\n"
        )

        # ── 2. Seq Scan on a large table (problem) ────────────────────────
        section("2. SEQ SCAN — large table WITHOUT index (problem)")
        print(
            "exp_orders has 50 000 rows. Querying a specific user_id with no\n"
            "index forces PostgreSQL to read the entire table.\n"
        )
        explain(
            cur,
            "WHERE user_id = 42  (no index — full table scan)",
            "SELECT * FROM exp_orders WHERE user_id = 42",
        )
        print(
            "WHAT TO LOOK FOR:\n"
            "  • Node type is 'Seq Scan' on a 50 000-row table.\n"
            "  • 'Rows Removed by Filter' will be ~49 950 — we fetched almost\n"
            "    everything just to discard it.\n"
            "  • Execution time grows linearly with table size.\n"
        )

        # ── 3. Index Scan on a large table (after adding index) ───────────
        section("3. INDEX SCAN — same query, with index added")
        cur.execute("CREATE INDEX exp_idx_orders_user ON exp_orders(user_id)")
        explain(
            cur,
            "WHERE user_id = 42  (B-tree index now present)",
            "SELECT * FROM exp_orders WHERE user_id = 42",
        )
        print(
            "WHAT TO LOOK FOR:\n"
            "  • Node type is now 'Index Scan' (or Bitmap Heap Scan).\n"
            "  • 'Index Cond: (user_id = 42)' — resolved by the index, not a Filter.\n"
            "  • 'Rows Removed by Filter' is 0 or absent — no wasted reads.\n"
            "  • Execution time is dramatically lower.\n"
        )

        # ── 4. Low selectivity → Seq Scan despite index ───────────────────
        section("4. SEQ SCAN — low selectivity (planner is right to ignore the index)")
        cur.execute("CREATE INDEX exp_idx_orders_status ON exp_orders(status)")
        explain(
            cur,
            "WHERE status = 'completed'  (~80% of rows match)",
            "SELECT * FROM exp_orders WHERE status = 'completed'",
        )
        print(
            "WHAT TO LOOK FOR:\n"
            "  • Node type is 'Seq Scan' even though an index on status exists.\n"
            "  • 80% of rows match — fetching them one-by-one via index causes more\n"
            "    random I/O than just reading the table sequentially.\n"
            "  • The planner is CORRECT. Don't add an index here expecting speedup.\n"
            "  • Indexes only help when the filter is SELECTIVE (few rows match).\n"
        )

        # ── 5. High selectivity comparison ───────────────────────────────
        section("5. HIGH SELECTIVITY — index used, low selectivity — seq scan chosen")
        explain(
            cur,
            "WHERE status = 'cancelled'  (~10% of rows match)",
            "SELECT * FROM exp_orders WHERE status = 'cancelled'",
        )
        print(
            "WHAT TO LOOK FOR:\n"
            "  • 'cancelled' is only 10% of rows (5 000 rows).\n"
            "  • PostgreSQL may use the index or a Bitmap Heap Scan here — it depends\n"
            "    on the cost estimate. Compare actual time to the 'completed' query.\n"
        )

        # ── 6. Stale statistics — wrong estimate ──────────────────────────
        section("6. STALE STATISTICS — estimated rows vs actual rows mismatch")
        print(
            "We insert 10 000 new 'refunded' orders WITHOUT running ANALYZE.\n"
            "The planner's statistics are now stale — it will underestimate rows.\n"
        )
        cur.execute(
            """
            INSERT INTO exp_orders (user_id, status, amount, created_at)
            SELECT
                (random() * 999 + 1)::INT,
                'refunded',
                (random() * 1000 + 1)::NUMERIC(10, 2),
                '2025-01-01'::DATE + (random() * 364)::INT
            FROM generate_series(1, 10000) i
            """
        )
        explain(
            cur,
            "WHERE status = 'refunded'  (statistics stale — before ANALYZE)",
            "SELECT count(*) FROM exp_orders WHERE status = 'refunded'",
        )
        print(
            "WHAT TO LOOK FOR:\n"
            "  • Compare 'rows=N' (estimate) vs 'actual rows=N' (real).\n"
            "  • The estimate will be far lower than the real count (~11 000).\n"
            "  • Bad estimates lead to bad plan choices (wrong join order, wrong\n"
            "    join type, index used when it shouldn't be, or vice versa).\n"
        )

        print("  → Running ANALYZE to refresh statistics...\n")
        cur.execute("ANALYZE exp_orders")

        explain(
            cur,
            "WHERE status = 'refunded'  (after ANALYZE — estimate corrected)",
            "SELECT count(*) FROM exp_orders WHERE status = 'refunded'",
        )
        print(
            "WHAT TO LOOK FOR:\n"
            "  • The estimated rows now closely match actual rows.\n"
            "  • Rule of thumb: run ANALYZE after bulk inserts/updates/deletes.\n"
            "  • autovacuum handles this automatically in production, but it can\n"
            "    lag behind during large data loads.\n"
        )

        # ── 7. Date range with GiST ───────────────────────────────────────
        section("7. DATE RANGE — Seq Scan vs B-tree range scan")
        explain(
            cur,
            "WHERE created_at BETWEEN ... (no index on created_at)",
            """
            SELECT count(*) FROM exp_orders
            WHERE created_at BETWEEN '2025-06-01' AND '2025-06-30'
            """,
        )
        cur.execute("CREATE INDEX exp_idx_orders_date ON exp_orders(created_at)")
        explain(
            cur,
            "WHERE created_at BETWEEN ... (B-tree index on created_at)",
            """
            SELECT count(*) FROM exp_orders
            WHERE created_at BETWEEN '2025-06-01' AND '2025-06-30'
            """,
        )
        print(
            "WHAT TO LOOK FOR:\n"
            "  • B-tree supports range queries — Index Scan or Bitmap Heap Scan.\n"
            "  • 'Index Cond' uses >= and <= — the index narrows the range directly.\n"
            "  • ~1/12 of rows match (one month). High enough selectivity to benefit.\n"
        )

        # ── Summary ────────────────────────────────────────────────────────
        section("DIAGNOSTIC CHECKLIST")
        print(
            "When you see a Seq Scan, ask:\n"
            "\n"
            "  1. Is the table small (<1 000 rows)?  → Seq Scan is correct.\n"
            "\n"
            "  2. Does the filter match most of the table (>~10–20%)?  → Seq Scan\n"
            "     is correct. An index would be slower due to random I/O.\n"
            "\n"
            "  3. Is there no index on the filtered column?  → Add one and\n"
            "     re-run EXPLAIN ANALYZE to confirm it's used.\n"
            "\n"
            "  4. Is 'rows=N' (estimate) very different from 'actual rows=N'?\n"
            "     → Run ANALYZE on the table to update statistics.\n"
            "\n"
            "  5. Is 'Rows Removed by Filter' very high?  → The index (if any)\n"
            "     is not filtering early enough; consider a more selective index\n"
            "     or a partial index (WHERE clause on the index itself).\n"
            "\n"
            "Golden rule: never guess — always EXPLAIN ANALYZE before and after\n"
            "adding an index. The planner sometimes surprises you.\n"
        )


if __name__ == "__main__":
    main()
