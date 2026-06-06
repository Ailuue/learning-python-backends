"""
Savepoints
==========
A savepoint is a named marker within a transaction. You can roll back to a
savepoint without aborting the entire transaction — only the work done after
that savepoint is undone.

Commands:
  SAVEPOINT <name>            — mark a position
  ROLLBACK TO SAVEPOINT <name> — undo everything since that marker
  RELEASE SAVEPOINT <name>    — discard the marker (doesn't commit anything)

Use case: batch processing where individual items can fail without
poisoning the entire batch. Without savepoints, a single bad row forces
a full rollback of everything processed so far.

Note: psycopg2 exposes savepoints via the connection object:
  conn.execute("SAVEPOINT sp")
  conn.execute("ROLLBACK TO SAVEPOINT sp")

Or equivalently through cursor.execute() — both work since SAVEPOINT is
a SQL statement, not a psycopg2-specific API.
"""

import psycopg2

import db


TRANSFERS = [
    ("Alice", "Bob",   200),   # valid
    ("Alice", "Carol", 5000),  # invalid — Alice won't have enough
    ("Bob",   "Carol",  50),   # valid
    ("Carol", "Bob",  9999),   # invalid — Carol won't have enough
    ("Bob",   "Alice",  75),   # valid
]


def process_without_savepoints() -> None:
    print("=" * 60)
    print("WITHOUT SAVEPOINTS — one bad transfer kills the batch")
    print("=" * 60)

    db.reset_accounts()

    print("Attempting 5 transfers in a single transaction:\n")

    conn = db.get_connection()
    cur = conn.cursor()

    success_count = 0
    try:
        for i, (sender, receiver, amount) in enumerate(TRANSFERS, 1):
            cur.execute(
                "UPDATE accounts SET balance = balance - %s WHERE owner = %s",
                (amount, sender),
            )
            cur.execute(
                "UPDATE accounts SET balance = balance + %s WHERE owner = %s",
                (amount, receiver),
            )
            print(f"  Transfer {i}: {sender} → {receiver}  ${amount}  ... queued")
            success_count += 1

        conn.commit()
        print(f"\n  Committed {success_count} transfers.")

    except psycopg2.errors.CheckViolation:
        conn.rollback()
        print(f"\n  CheckViolation on transfer {i} — entire batch rolled back.")
        print(f"  {success_count} valid transfers were lost.\n")

    conn.close()

    print("Balances after failed batch:")
    with db.cursor() as c:
        db.print_table(c, "SELECT owner, balance FROM accounts ORDER BY id",
                       ["owner", "balance"])


def process_with_savepoints() -> None:
    print("=" * 60)
    print("WITH SAVEPOINTS — bad transfers skipped, good ones kept")
    print("=" * 60)

    db.reset_accounts()

    print("Same 5 transfers, but each wrapped in its own savepoint:\n")

    conn = db.get_connection()
    cur = conn.cursor()

    succeeded = []
    skipped = []

    for i, (sender, receiver, amount) in enumerate(TRANSFERS, 1):
        cur.execute(f"SAVEPOINT sp_{i}")
        try:
            cur.execute(
                "UPDATE accounts SET balance = balance - %s WHERE owner = %s",
                (amount, sender),
            )
            cur.execute(
                "UPDATE accounts SET balance = balance + %s WHERE owner = %s",
                (amount, receiver),
            )
            # Discard the savepoint — no longer need a rollback target for this item
            cur.execute(f"RELEASE SAVEPOINT sp_{i}")
            succeeded.append((sender, receiver, amount))
            print(f"  Transfer {i}: {sender} → {receiver}  ${amount}  ✓ queued")

        except psycopg2.errors.CheckViolation:
            # Roll back only to the savepoint — prior work in this transaction is intact
            cur.execute(f"ROLLBACK TO SAVEPOINT sp_{i}")
            skipped.append((sender, receiver, amount))
            print(f"  Transfer {i}: {sender} → {receiver}  ${amount}  ✗ skipped (insufficient funds)")

    conn.commit()
    conn.close()

    print(f"\n  Committed {len(succeeded)} transfers, skipped {len(skipped)}.\n")

    print("Balances after partial batch:")
    with db.cursor() as c:
        db.print_table(c, "SELECT owner, balance FROM accounts ORDER BY id",
                       ["owner", "balance"])

    print(
        "The three valid transfers committed together even though they share\n"
        "a transaction with two failed ones. The savepoints let us peel off\n"
        "the bad work without touching the good work.\n"
    )


def main() -> None:
    process_without_savepoints()
    process_with_savepoints()


if __name__ == "__main__":
    main()
