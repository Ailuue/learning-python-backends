"""
Cache Invalidation Strategies
===============================
Phil Karlton's famous remark: "There are only two hard things in Computer
Science: cache invalidation and naming things."

The challenge: keeping the cache consistent with the database.
Three main strategies:

  1. TTL-based  — let time do it. Set a short TTL and accept that cached data
                  is stale for up to TTL seconds. Simple, always works, but
                  guarantees a window of inconsistency.

  2. Event-driven — explicitly DELETE (or UPDATE) the cache entry when the
                  source data changes. Zero staleness window. Requires all
                  write paths to know about the cache.

  3. Versioned keys — embed a version number in the key. Incrementing the
                  version "logically deletes" all old keys without touching
                  them. The old entries decay naturally via TTL. Useful when
                  many keys are related and you want bulk invalidation.

This script demonstrates all three and shows the trade-offs.
"""

import time

import cache
import db
from db import Product

# ---------------------------------------------------------------------------
# Strategy 1: TTL-based
# ---------------------------------------------------------------------------

def demo_ttl_based():
    print("\n=== Strategy 1: TTL-based invalidation ===")
    print("""
  Set a short TTL. Stale data exists for at most TTL seconds.
  No code needed at write time — the cache expires itself.
  Trade-off: you tolerate a window of inconsistency.
""")

    db.reset_schema()
    cache.flush_all()

    with db.get_session() as session:
        products = db.seed(session)
        keyboard = products[0]

    # Cache with a very short TTL for the demo
    short_ttl = 4
    key = cache.product_key(keyboard.id)
    cache.setex(key, short_ttl, cache.serialise(keyboard))
    print(f"  Cached {key!r} with TTL={short_ttl}s")

    # Simulate a DB update that bypasses the cache
    with db.get_session() as session:
        p = session.get(Product, keyboard.id)
        p.price = "999.99"
        session.commit()
    print("  DB updated (price → 999.99) — cache still has old price")

    cached = cache.deserialise(cache.get(key))
    print(f"  Cache price: {cached['price']}  (stale!)")

    print(f"  Waiting {short_ttl}s for TTL expiry...")
    time.sleep(short_ttl + 1)

    result = cache.get(key)
    print(f"  After TTL expiry: {result}  (MISS — next read will refresh)")


# ---------------------------------------------------------------------------
# Strategy 2: Event-driven (explicit invalidation)
# ---------------------------------------------------------------------------

def demo_event_driven():
    print("\n\n=== Strategy 2: Event-driven invalidation ===")
    print("""
  Delete (or update) the cache key at the point of the DB write.
  No staleness window. Every write path must remember to do this.
  Trade-off: cache coupling — all writers must know the cache key schema.
""")

    db.reset_schema()
    cache.flush_all()

    with db.get_session() as session:
        products = db.seed(session)
        hub = products[1]

    # Warm the cache
    key = cache.product_key(hub.id)
    cache.setex(key, 60, cache.serialise(hub))
    print(f"  Cached {key!r}")

    # Write path that correctly invalidates the cache
    def update_price_with_invalidation(session, product_id: int, new_price) -> None:
        product = session.get(Product, product_id)
        product.price = new_price
        session.commit()
        # Invalidate the cache — no staleness window
        cache.delete(cache.product_key(product_id))
        print(f"  DB updated + cache DEL {cache.product_key(product_id)!r}")

    with db.get_session() as session:
        update_price_with_invalidation(session, hub.id, "39.99")

    result = cache.get(key)
    print(f"  Cache after write: {result}  (MISS — immediately consistent)")

    # The danger: a write path that forgets to invalidate
    print("""
  ⚠  The failure mode: a write path that updates the DB but forgets to delete
     the cache key. The cache serves stale data indefinitely (until TTL).
     Mitigation: centralise all cache operations in a single service layer so
     there's only one place that can forget.
""")


# ---------------------------------------------------------------------------
# Strategy 3: Versioned keys
# ---------------------------------------------------------------------------

# A simple in-memory version counter for the demo.
# In production this would be stored in Redis itself (INCR command).
_version: dict[str, int] = {}

def get_version(namespace: str) -> int:
    return _version.get(namespace, 1)

def bump_version(namespace: str) -> int:
    _version[namespace] = _version.get(namespace, 1) + 1
    return _version[namespace]

def versioned_key(namespace: str, item_id: int) -> str:
    v = get_version(namespace)
    return f"{namespace}:v{v}:{item_id}"


def demo_versioned_keys():
    print("\n\n=== Strategy 3: Versioned keys ===")
    print("""
  Embed a version number in every cache key.
  To invalidate a whole category, increment the version.
  Old keys become unreachable immediately and decay via TTL on their own.
  Avoids scanning for keys to delete (which is expensive at scale).
""")

    db.reset_schema()
    cache.flush_all()

    with db.get_session() as session:
        db.seed(session)

    # Cache all three products under version 1
    with db.get_session() as session:
        for p in session.query(Product).all():
            key = versioned_key("product", p.id)
            cache.setex(key, 60, cache.serialise(p))
            print(f"  Cached {key!r}")

    print(f"\n  Current version: {get_version('product')}")

    # Simulate a bulk update — e.g. a 20% sale on all products
    print("\n  Running bulk price update (20% discount)...")
    with db.get_session() as session:
        for p in session.query(Product).all():
            p.price = round(float(p.price) * 0.8, 2)
        session.commit()

    # Instead of finding and deleting individual keys, just bump the version.
    # All existing cache entries become unreachable instantly.
    new_v = bump_version("product")
    print(f"  Version bumped to {new_v}")
    print(f"  Old keys (v{new_v - 1}:*) are now unreachable — they'll expire via TTL")

    # Next read misses (new version key doesn't exist) and re-populates
    with db.get_session() as session:
        for p in session.query(Product).all():
            key = versioned_key("product", p.id)
            raw = cache.get(key)
            if raw is None:
                print(f"  MISS {key!r}  → DB fallback → re-cached")
                cache.setex(key, 60, cache.serialise(p))
            else:
                print(f"  HIT  {key!r}")

    print(f"\n  All products now cached under version {new_v} with updated prices.")

    print("""
  Trade-off:
    - Old versioned keys take up memory until their TTL expires.
    - The version counter is a shared dependency — store it in Redis with
      INCR so all app instances agree.
    - Granularity: you can version individual resources, categories, or the
      whole cache namespace depending on how related the data is.
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    demo_ttl_based()
    demo_event_driven()
    demo_versioned_keys()

    print("\n=== Summary ===")
    print("""
  Strategy          Consistency    Complexity    Best for
  ────────────────  ─────────────  ────────────  ──────────────────────────────
  TTL-based         Eventually     Low           Data where brief staleness is OK
  Event-driven      Immediate      Medium        Critical data, single write path
  Versioned keys    Immediate      Medium        Bulk invalidation, related keys
""")


if __name__ == "__main__":
    main()
