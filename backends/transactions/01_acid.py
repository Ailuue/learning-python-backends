"""
ACID Properties
===============
Every database transaction must satisfy four guarantees:

  Atomicity    — the transaction is all-or-nothing. If any statement fails,
                 every change made so far in that transaction is rolled back.

  Consistency  — the transaction can only bring the database from one valid
                 state to another. Constraints (CHECK, FK, UNIQUE) are
                 enforced at commit time; a violation aborts the whole thing.

  Isolation    — concurrent transactions behave as if they ran one at a time.
                 The degree of isolation is configurable — see 02_isolation.py.

  Durability   — once committed, data survives crashes. PostgreSQL achieves
                 this via Write-Ahead Logging (WAL): changes are written to
                 the WAL on disk before the commit returns to the client.
                 Durability cannot be demonstrated in a script, but it's why
                 `COMMIT` can be slow on spinning disks.

Domain: bank accounts. Schema: accounts(id, owner, balance CHECK balance >= 0)
"""

import psycopg2

import db


def demo_atomicity_success() -> None:
    print("=" * 60)
    print("ATOMICITY — successful transfer")
    print("=" * 60)

    db.reset_accounts()

    conn = db.get_connection()
    cur = conn.cursor()

    print("Before:")
    with db.cursor() as c:
        db.print_table(c, "SELECT owner, balance FROM accounts ORDER BY id",
                       ["owner", "balance"])

    # Both statements succeed — the transaction commits as a unit
    cur.execute("UPDATE accounts SET balance = balance - 200 WHERE owner = 'Alice'")
    cur.execute("UPDATE accounts SET balance = balance + 200 WHERE owner = 'Bob'")
    conn.commit()
    conn.close()

    print("After transferring $200 from Alice to Bob:")
    with db.cursor() as c:
        db.print_table(c, "SELECT owner, balance FROM accounts ORDER BY id",
                       ["owner", "balance"])
    print("Both rows updated together — neither can commit without the other.\n")


def demo_atomicity_failure() -> None:
    print("=" * 60)
    print("ATOMICITY — failed transfer rolls back completely")
    print("=" * 60)

    db.reset_accounts()

    conn = db.get_connection()
    cur = conn.cursor()

    print("Attempting to transfer $1500 from Alice (balance: $1000)...")
    print("The debit executes first and appears to succeed in isolation.")
    print("The credit then violates the CHECK (balance >= 0) on Alice's account.\n")

    try:
        cur.execute("UPDATE accounts SET balance = balance - 1500 WHERE owner = 'Alice'")
        # This next statement is fine — Bob is getting money
        cur.execute("UPDATE accounts SET balance = balance + 1500 WHERE owner = 'Bob'")
        # But the debit left Alice at -500, which the CHECK constraint will catch at commit
        conn.commit()
    except psycopg2.errors.CheckViolation as e:
        conn.rollback()
        print(f"Transaction rolled back: {e.pgerror.strip()}\n")

    conn.close()

    print("Balances after the failed transfer:")
    with db.cursor() as c:
        db.print_table(c, "SELECT owner, balance FROM accounts ORDER BY id",
                       ["owner", "balance"])
    print("Both rows are unchanged. The rollback undid the debit even though")
    print("the debit statement itself didn't raise an error.\n")


def demo_consistency() -> None:
    print("=" * 60)
    print("CONSISTENCY — constraints enforce valid state")
    print("=" * 60)

    db.reset_accounts()

    print("Attempting to INSERT an account with a negative balance directly...\n")

    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO accounts (owner, balance) VALUES ('Eve', -100)")
        conn.commit()
    except psycopg2.errors.CheckViolation as e:
        conn.rollback()
        print(f"Rejected: {e.pgerror.strip()}\n")
    conn.close()

    print("The CHECK constraint is not optional — it fires whether the bad value")
    print("comes from application code, a migration, or a direct SQL statement.\n")
    print("Constraints are the database's way of making certain invalid states")
    print("literally unreachable, regardless of what the application does.\n")


def main() -> None:
    demo_atomicity_success()
    demo_atomicity_failure()
    demo_consistency()


if __name__ == "__main__":
    main()
