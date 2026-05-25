"""
Docker Compose Practice API
============================
Three services work together here, each reachable via its Compose service name:
  - This app:    app:8000
  - PostgreSQL:  db:5432
  - Redis:       redis:6379

Connection strings come from environment variables set in docker-compose.yml.
"""

import json
import os
from contextlib import contextmanager

import psycopg2
import redis as redis_lib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Docker Compose Practice API")

_redis = redis_lib.from_url(
    os.environ.get("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True,
)

ITEMS_CACHE_KEY = "items:all"
CACHE_TTL = 30  # seconds — short so you can watch the cache expire


@contextmanager
def get_db():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        yield conn
    finally:
        conn.close()


class ItemCreate(BaseModel):
    name: str
    description: str | None = None


@app.get("/")
def root():
    return {
        "message": "Docker Compose Practice API",
        "env": os.environ.get("APP_ENV", "production"),
    }


@app.get("/health")
def health():
    """Check that both DB and Redis are reachable. Useful for depends_on health checks."""
    db_ok = False
    redis_ok = False

    try:
        with get_db() as conn:
            conn.cursor().execute("SELECT 1")
        db_ok = True
    except Exception:
        pass

    try:
        _redis.ping()
        redis_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "db": db_ok,
        "redis": redis_ok,
    }


@app.get("/items")
def list_items():
    """
    Returns items from Redis cache if available; falls back to PostgreSQL.
    The 'source' field tells you which path was taken — watch it change
    on the first request after cache expiry (CACHE_TTL seconds).
    """
    cached = _redis.get(ITEMS_CACHE_KEY)
    if cached:
        return {"items": json.loads(cached), "source": "cache"}

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, description, created_at::text FROM items ORDER BY id"
        )
        rows = cur.fetchall()

    items = [
        {"id": r[0], "name": r[1], "description": r[2], "created_at": r[3]}
        for r in rows
    ]
    _redis.setex(ITEMS_CACHE_KEY, CACHE_TTL, json.dumps(items))
    return {"items": items, "source": "db"}


@app.post("/items", status_code=201)
def create_item(item: ItemCreate):
    """Insert a new item and immediately invalidate the Redis cache."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO items (name, description) VALUES (%s, %s) RETURNING id",
            (item.name, item.description),
        )
        item_id = cur.fetchone()[0]
        conn.commit()

    _redis.delete(ITEMS_CACHE_KEY)  # next GET /items will re-query the DB
    return {"id": item_id, "name": item.name, "description": item.description}


@app.delete("/items/cache")
def bust_cache():
    """Manually invalidate the cache — useful for seeing cache vs db source."""
    _redis.delete(ITEMS_CACHE_KEY)
    return {"message": "cache cleared"}
