"""
Isolation Levels
================
"Isolation" in ACID is not binary — it's a dial. SQL defines four levels,
each preventing a different class of anomaly. PostgreSQL implements three
(READ UNCOMMITTED is silently promoted to READ COMMITTED):

  Level               | Dirty read | Non-repeatable read | Phantom read | Write skew
  ------------------- | ---------- | ------------------- | ------------ | ----------
  READ COMMITTED      | prevented  | possible            | possible     | possible
  REPEATABLE READ     | prevented  | prevented           | prevented*   | possible
  SERIALIZABLE        | prevented  | prevented           | prevented    | prevented

  * PostgreSQL's REPEATABLE READ also prevents phantom reads, which is
    stronger than the SQL standard requires.

Higher isolation = fewer anomalies but more lock contention and a higher
chance of serialization errors that the application must retry.

The default in PostgreSQL is READ COMMITTED.

Anomaly definitions:
  Dirty read           — reading another transaction's uncommitted changes.
  Non-repeatable read  — reading the same row twice gets different values
                         because another transaction updated it between reads.
  Phantom read         — re-running a range query returns different rows
                         because another transaction inserted or deleted rows.
  Write skew           — two transactions both read a value, make a decision
                         based on it, and both write — invalidating each
                         other's assumption. Neither wrote a "dirty" value,
                         but the combination breaks an invariant.

Two independent connections (conn_a, conn_b) simulate two concurrent sessions.
Steps are interleaved manually to reproduce each anomaly precisely.
"""

import psycopg2

import db


def demo_non_repeatable_read() -> None:
    print("=" * 60)
    print("NON-REPEATABLE READ — READ COMMITTED allows it")
    print("=" * 60)

    db.reset_accounts()

    print(
        "Scenario: Transaction A reads Alice's balance twice.\n"
        "          Transaction B updates Alice's balance between those reads.\n"
    )

    with db.two_connections() as (conn_a, conn_b):
        cur_a = conn_a.cursor()
        cur_b = conn_b.cursor()

        # Explicitly set READ COMMITTED (it's the default, but stated for clarity)
        cur_a.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")

        cur_a.execute("SELECT balance FROM accounts WHERE owner = 'Alice'")
        balance_first = cur_a.fetchone()[0]
        print(f"  Tx A reads Alice's balance:        ${balance_first}")

        cur_b.execute("UPDATE accounts SET balance = balance - 300 WHERE owner = 'Alice'")
        conn_b.commit()
        print(f"  Tx B updates Alice: -$300 and COMMITS")

        cur_a.execute("SELECT balance FROM accounts WHERE owner = 'Alice'")
        balance_second = cur_a.fetchone()[0]
        print(f"  Tx A reads Alice's balance again:  ${balance_second}  ← DIFFERENT\n")

        conn_a.commit()

    print(
        "Tx A saw two different values for the same row within one transaction.\n"
        "This is a non-repeatable read. Under READ COMMITTED, each SELECT\n"
        "sees a fresh snapshot of committed data — even mid-transaction.\n"
    )


def demo_repeatable_read_prevents_it() -> None:
    print("=" * 60)
    print("REPEATABLE READ — snapshot is frozen at transaction start")
    print("=" * 60)

    db.reset_accounts()

    print(
        "Same scenario, but Tx A uses REPEATABLE READ.\n"
    )

    with db.two_connections() as (conn_a, conn_b):
        cur_a = conn_a.cursor()
        cur_b = conn_b.cursor()

        cur_a.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")

        cur_a.execute("SELECT balance FROM accounts WHERE owner = 'Alice'")
        balance_first = cur_a.fetchone()[0]
        print(f"  Tx A reads Alice's balance:        ${balance_first}")

        cur_b.execute("UPDATE accounts SET balance = balance - 300 WHERE owner = 'Alice'")
        conn_b.commit()
        print(f"  Tx B updates Alice: -$300 and COMMITS")

        cur_a.execute("SELECT balance FROM accounts WHERE owner = 'Alice'")
        balance_second = cur_a.fetchone()[0]
        print(f"  Tx A reads Alice's balance again:  ${balance_second}  ← SAME\n")

        conn_a.commit()

    print(
        "Tx A sees the same value both times. REPEATABLE READ takes a snapshot\n"
        "of the entire database at the moment the transaction's first query runs.\n"
        "All subsequent reads in that transaction use that snapshot, regardless\n"
        "of what other transactions commit.\n"
    )


def demo_write_skew() -> None:
    print("=" * 60)
    print("WRITE SKEW — REPEATABLE READ does not prevent it")
    print("=" * 60)

    db.reset_doctors()

    print(
        "Scenario: A hospital requires at least one doctor on-call at all times.\n"
        "          Alice and Bob are both on-call. Both want to go off-call.\n"
        "          Each checks: 'are there at least 2 on-call?' before deciding.\n"
    )

    with db.two_connections() as (conn_a, conn_b):
        cur_a = conn_a.cursor()
        cur_b = conn_b.cursor()

        cur_a.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        cur_b.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")

        # Both transactions check the on-call count from their own snapshot
        cur_a.execute("SELECT COUNT(*) FROM doctors WHERE on_call = TRUE")
        count_a = cur_a.fetchone()[0]
        print(f"  Tx A (Alice) sees {count_a} doctors on-call — safe to go off-call")

        cur_b.execute("SELECT COUNT(*) FROM doctors WHERE on_call = TRUE")
        count_b = cur_b.fetchone()[0]
        print(f"  Tx B (Bob)   sees {count_b} doctors on-call — safe to go off-call")

        # Both write based on their (now stale) decision
        cur_a.execute("UPDATE doctors SET on_call = FALSE WHERE name = 'Alice'")
        conn_a.commit()
        print("  Tx A sets Alice off-call and COMMITS")

        cur_b.execute("UPDATE doctors SET on_call = FALSE WHERE name = 'Bob'")
        conn_b.commit()
        print("  Tx B sets Bob off-call and COMMITS\n")

    print("Result:")
    with db.cursor() as c:
        db.print_table(c, "SELECT name, on_call FROM doctors ORDER BY id",
                       ["name", "on_call"])

    print(
        "Nobody is on-call. Both transactions read a consistent snapshot,\n"
        "made a locally valid decision, and committed — but the combination\n"
        "of their writes violated the invariant. This is write skew.\n"
        "REPEATABLE READ prevents dirty and non-repeatable reads, but it\n"
        "cannot detect that two transactions' decisions conflict.\n"
    )


def demo_serializable_prevents_write_skew() -> None:
    print("=" * 60)
    print("SERIALIZABLE — detects and aborts conflicting transactions")
    print("=" * 60)

    db.reset_doctors()

    print(
        "Same scenario. Both transactions use SERIALIZABLE this time.\n"
    )

    with db.two_connections() as (conn_a, conn_b):
        cur_a = conn_a.cursor()
        cur_b = conn_b.cursor()

        cur_a.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        cur_b.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")

        cur_a.execute("SELECT COUNT(*) FROM doctors WHERE on_call = TRUE")
        count_a = cur_a.fetchone()[0]
        print(f"  Tx A (Alice) sees {count_a} doctors on-call — tries to go off-call")

        cur_b.execute("SELECT COUNT(*) FROM doctors WHERE on_call = TRUE")
        count_b = cur_b.fetchone()[0]
        print(f"  Tx B (Bob)   sees {count_b} doctors on-call — tries to go off-call")

        cur_a.execute("UPDATE doctors SET on_call = FALSE WHERE name = 'Alice'")
        conn_a.commit()
        print("  Tx A commits successfully")

        try:
            cur_b.execute("UPDATE doctors SET on_call = FALSE WHERE name = 'Bob'")
            conn_b.commit()
        except psycopg2.errors.SerializationFailure:
            conn_b.rollback()
            print("  Tx B got a serialization error — rolled back\n")

    print("Result:")
    with db.cursor() as c:
        db.print_table(c, "SELECT name, on_call FROM doctors ORDER BY id",
                       ["name", "on_call"])

    print(
        "Alice went off-call, but Bob's transaction was aborted.\n"
        "PostgreSQL detected that the two transactions' read/write sets conflicted\n"
        "in a way that has no valid serial ordering — so it aborted one of them.\n\n"
        "IMPORTANT: The application must handle SerializationFailure by retrying\n"
        "the entire transaction from scratch. This is not optional — it's part of\n"
        "the contract when using SERIALIZABLE isolation.\n"
    )


def main() -> None:
    demo_non_repeatable_read()
    demo_repeatable_read_prevents_it()
    demo_write_skew()
    demo_serializable_prevents_write_skew()


if __name__ == "__main__":
    main()
