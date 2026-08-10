"""
Row-Level Locking
=================
PostgreSQL automatically acquires row locks during UPDATE and DELETE.
Sometimes you need to lock rows that you're about to update but haven't
changed yet — to prevent another transaction from modifying them in
between your read and your write (the TOCTOU problem).

Two locking clauses:

  SELECT ... FOR UPDATE
    Locks the selected rows immediately. Any other transaction that tries
    to SELECT FOR UPDATE (or UPDATE/DELETE) the same rows will block
    until the first transaction commits or rolls back.
    Use when: you read a value, then later update it in the same transaction.

  SELECT ... FOR UPDATE SKIP LOCKED
    Like FOR UPDATE, but instead of blocking, it simply skips any rows
    that are already locked by another transaction.
    Use when: multiple workers pull items from a queue concurrently.

TOCTOU = Time-of-Check to Time-of-Use.
The gap between reading a value and acting on it is a race window.
SELECT FOR UPDATE closes that window.
"""

import db


def demo_toctou_problem() -> None:
    print("=" * 60)
    print("TOCTOU PROBLEM — the race between read and write")
    print("=" * 60)

    db.reset_inventory()

    print(
        "Scenario: Two customers both try to buy the last Widget (stock = 1).\n"
        "          Without locking, both see stock = 1 and decide to proceed.\n"
    )

    with db.two_connections() as (conn_a, conn_b):
        cur_a = conn_a.cursor()
        cur_b = conn_b.cursor()

        # Both transactions read stock — neither is locked
        cur_a.execute("SELECT stock FROM inventory WHERE product = 'Widget'")
        stock_a = db.scalar(cur_a)
        print(f"  Customer A reads stock = {stock_a}  → decides to purchase")

        cur_b.execute("SELECT stock FROM inventory WHERE product = 'Widget'")
        stock_b = db.scalar(cur_b)
        print(f"  Customer B reads stock = {stock_b}  → also decides to purchase")

        print()
        print(
            "  Both saw stock = 1 and both will now try to decrement it.\n"
            "  In production this means two orders for one item — an oversell.\n"
            "  (Our CHECK constraint will catch the second decrement here, but\n"
            "  without it the database would silently go to stock = -1.)\n"
        )

        conn_a.rollback()
        conn_b.rollback()


def demo_select_for_update() -> None:
    print("=" * 60)
    print("SELECT FOR UPDATE — lock the row at read time")
    print("=" * 60)

    db.reset_inventory()

    print(
        "Same scenario. Customer A uses SELECT FOR UPDATE.\n"
        "Customer B's lock attempt is serialized — it waits for A to commit,\n"
        "then reads the already-decremented stock.\n"
    )

    with db.two_connections() as (conn_a, conn_b):
        cur_a = conn_a.cursor()
        cur_b = conn_b.cursor()

        # A locks the row immediately on read
        cur_a.execute(
            "SELECT stock FROM inventory WHERE product = 'Widget' FOR UPDATE"
        )
        stock_a = db.scalar(cur_a)
        print(f"  Customer A reads stock = {stock_a}  (row is now locked)")

        # A decrements and commits — releasing the lock
        cur_a.execute(
            "UPDATE inventory SET stock = stock - 1 WHERE product = 'Widget'"
        )
        conn_a.commit()
        print("  Customer A decrements stock to 0 and COMMITS (lock released)\n")

        # B can now acquire the lock — reads the post-commit value
        cur_b.execute(
            "SELECT stock FROM inventory WHERE product = 'Widget' FOR UPDATE"
        )
        stock_b = db.scalar(cur_b)
        print(f"  Customer B reads stock = {stock_b}  (after A's commit)")

        if stock_b > 0:
            cur_b.execute(
                "UPDATE inventory SET stock = stock - 1 WHERE product = 'Widget'"
            )
            conn_b.commit()
            print("  Customer B purchases — stock decremented")
        else:
            conn_b.rollback()
            print("  Customer B sees stock = 0 — purchase rejected\n")

    print("Final inventory:")
    with db.cursor() as c:
        db.print_table(c, "SELECT product, stock FROM inventory",
                       ["product", "stock"])

    print(
        "SELECT FOR UPDATE turns the read into part of the same atomic unit\n"
        "as the write. The lock is held until COMMIT, so no other transaction\n"
        "can read-and-modify the row in between.\n"
    )


def demo_skip_locked() -> None:
    print("=" * 60)
    print("SKIP LOCKED — parallel workers claiming jobs without blocking")
    print("=" * 60)

    db.reset_jobs()

    print(
        "Scenario: Two workers pull jobs from a queue simultaneously.\n"
        "          SKIP LOCKED lets each worker grab a different job\n"
        "          instead of blocking on the same one.\n"
    )

    with db.two_connections() as (conn_a, conn_b):
        cur_a = conn_a.cursor()
        cur_b = conn_b.cursor()

        # Worker A claims a job — job-1 is now locked by conn_a's transaction
        cur_a.execute("""
            SELECT id, payload FROM jobs
            WHERE status = 'pending'
            ORDER BY id
            FOR UPDATE SKIP LOCKED
            LIMIT 1
        """)
        job_a = db.one(cur_a)
        cur_a.execute(
            "UPDATE jobs SET status = 'processing' WHERE id = %s", (job_a[0],)
        )
        print(f"  Worker A claims: id={job_a[0]}  payload={job_a[1]!r}")

        # Worker B runs the same query — job-1 is locked so it's skipped,
        # B gets job-2 without blocking
        cur_b.execute("""
            SELECT id, payload FROM jobs
            WHERE status = 'pending'
            ORDER BY id
            FOR UPDATE SKIP LOCKED
            LIMIT 1
        """)
        job_b = db.one(cur_b)
        cur_b.execute(
            "UPDATE jobs SET status = 'processing' WHERE id = %s", (job_b[0],)
        )
        print(f"  Worker B claims: id={job_b[0]}  payload={job_b[1]!r}")

        print()
        print("  Both workers claimed different jobs with no blocking.\n")

        cur_a.execute("UPDATE jobs SET status = 'done' WHERE id = %s", (job_a[0],))
        cur_b.execute("UPDATE jobs SET status = 'done' WHERE id = %s", (job_b[0],))
        conn_a.commit()
        conn_b.commit()

    print("Jobs table after both workers finish:")
    with db.cursor() as c:
        db.print_table(c, "SELECT id, payload, status FROM jobs ORDER BY id",
                       ["id", "payload", "status"])

    print(
        "Without SKIP LOCKED, Worker B would have blocked until Worker A committed,\n"
        "then seen that job-1 was already claimed. SKIP LOCKED removes the wait\n"
        "entirely — it's the standard pattern for building job queues in Postgres.\n"
    )


def main() -> None:
    demo_toctou_problem()
    demo_select_for_update()
    demo_skip_locked()


if __name__ == "__main__":
    main()
