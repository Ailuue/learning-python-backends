"""
Redis client and key-building helpers shared across all scripts.

Key naming convention:
  product:{id}          — a single cached product (JSON string)
  products:list         — cached list of all products
  lock:product:{id}     — distributed lock for stampede protection
  pending:writes        — Redis list used by write-behind to queue pending DB flushes
"""

import json
import os

import redis
from dotenv import load_dotenv

load_dotenv()

_client: redis.Redis = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    decode_responses=True,
)

# TTL values kept short so demo output stays readable.
# In production these would be minutes to hours.
PRODUCT_TTL   = 10   # seconds — single product entry
LIST_TTL      = 5    # seconds — list result (shorter because it goes stale faster)
LOCK_TTL      = 2    # seconds — stampede lock hold time


# ---------------------------------------------------------------------------
# Key constructors
# ---------------------------------------------------------------------------

def product_key(product_id: int) -> str:
    return f"product:{product_id}"

def list_key() -> str:
    return "products:list"

def lock_key(product_id: int) -> str:
    return f"lock:product:{product_id}"

def pending_writes_key() -> str:
    return "pending:writes"


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------
# Decimal doesn't serialise to JSON natively, so we convert via str.

def _product_to_dict(product) -> dict:
    return {
        "id":    product.id,
        "name":  product.name,
        "price": str(product.price),
        "stock": product.stock,
    }

def serialise(product) -> str:
    return json.dumps(_product_to_dict(product))

def deserialise(raw: str) -> dict:
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------

def get(key: str) -> str | None:
    return _client.get(key)

def setex(key: str, ttl: int, value: str) -> None:
    _client.setex(key, ttl, value)

def delete(*keys: str) -> None:
    _client.delete(*keys)

def ttl(key: str) -> int:
    return _client.ttl(key)

def exists(key: str) -> bool:
    return bool(_client.exists(key))

def pipeline():
    return _client.pipeline()

def rpush(key: str, value: str) -> None:
    _client.rpush(key, value)

def lrange(key: str, start: int, end: int) -> list[str]:
    return _client.lrange(key, start, end)

def ltrim(key: str, start: int, end: int) -> None:
    _client.ltrim(key, start, end)

def llen(key: str) -> int:
    return _client.llen(key)

def set_nx(key: str, value: str, ex: int) -> bool:
    """SET key value NX EX ex — returns True if key was set (lock acquired)."""
    return bool(_client.set(key, value, nx=True, ex=ex))

def flush_all() -> None:
    """Delete every key in Redis. Only used at the top of each demo."""
    _client.flushdb()


# ---------------------------------------------------------------------------
# Pretty print helper
# ---------------------------------------------------------------------------

def print_cache_state(label: str = "Cache state", *keys: str) -> None:
    if not keys:
        return
    print(f"\n  [{label}]")
    for key in keys:
        raw = get(key)
        if raw is None:
            remaining = ttl(key)
            print(f"    {key!r:35s}  MISS")
        else:
            remaining = ttl(key)
            ttl_str = f"TTL={remaining}s" if remaining >= 0 else "no TTL"
            short = raw if len(raw) < 80 else raw[:77] + "..."
            print(f"    {key!r:35s}  HIT  ({ttl_str})  {short}")
