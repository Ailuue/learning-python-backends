import os
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection(autocommit: bool = False) -> psycopg2.extensions.connection:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "transactions_demo"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )
    conn.autocommit = autocommit
    return conn


@contextmanager
def cursor():
    """Single connection, auto-commit/rollback. Used for schema setup and resets."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()


@contextmanager
def two_connections():
    """Two independent connections for demonstrating concurrent transactions."""
    conn_a = get_connection()
    conn_b = get_connection()
    try:
        yield conn_a, conn_b
    finally:
        for conn in (conn_a, conn_b):
            try:
                conn.rollback()
            except Exception:
                pass
            conn.close()


def setup_schema() -> None:
    with cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id      SERIAL PRIMARY KEY,
                owner   TEXT NOT NULL,
                balance NUMERIC(12, 2) NOT NULL CHECK (balance >= 0)
            );

            CREATE TABLE IF NOT EXISTS doctors (
                id      SERIAL PRIMARY KEY,
                name    TEXT NOT NULL,
                on_call BOOLEAN NOT NULL DEFAULT TRUE
            );

            CREATE TABLE IF NOT EXISTS inventory (
                id      SERIAL PRIMARY KEY,
                product TEXT NOT NULL,
                stock   INT  NOT NULL CHECK (stock >= 0)
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id      SERIAL PRIMARY KEY,
                payload TEXT NOT NULL,
                status  TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'processing', 'done'))
            );
        """)


def reset_accounts() -> None:
    with cursor() as cur:
        cur.execute("TRUNCATE accounts RESTART IDENTITY")
        cur.execute("""
            INSERT INTO accounts (owner, balance) VALUES
                ('Alice', 1000),
                ('Bob',    500),
                ('Carol',  250)
        """)


def reset_doctors() -> None:
    with cursor() as cur:
        cur.execute("TRUNCATE doctors RESTART IDENTITY")
        cur.execute("""
            INSERT INTO doctors (name, on_call) VALUES
                ('Alice', TRUE),
                ('Bob',   TRUE)
        """)


def reset_inventory() -> None:
    with cursor() as cur:
        cur.execute("TRUNCATE inventory RESTART IDENTITY")
        cur.execute("INSERT INTO inventory (product, stock) VALUES ('Widget', 1)")


def reset_jobs() -> None:
    with cursor() as cur:
        cur.execute("TRUNCATE jobs RESTART IDENTITY")
        cur.execute("""
            INSERT INTO jobs (payload) VALUES
                ('job-1'), ('job-2'), ('job-3'), ('job-4'), ('job-5')
        """)


def print_table(cur, query: str, headers: list[str], params=None) -> None:
    cur.execute(query, params)
    rows = cur.fetchall()
    widths = [
        max(len(h), max((len(str(r[i])) for r in rows), default=0))
        for i, h in enumerate(headers)
    ]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt.format(*[str(v) if v is not None else "NULL" for v in row]))
    print()


setup_schema()
