import os
from contextlib import contextmanager

import psycopg2
from fastapi import FastAPI

app = FastAPI()


@contextmanager
def get_db():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        yield conn
    finally:
        conn.close()


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/items")
def items():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM items ORDER BY id")
        rows = cur.fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]


@app.get("/health")
def health():
    try:
        with get_db() as conn:
            conn.cursor().execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": db_ok}
