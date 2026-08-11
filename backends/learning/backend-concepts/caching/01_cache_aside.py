"""
Cache-Aside (Lazy Loading)
===========================
The most common caching pattern. The application manages the cache manually:
read from cache first, fall back to DB on a miss, write-back to cache.

                  ┌──────────────┐
    READ request  │              │  cache HIT  → return cached value
    ─────────────▶│  Application │────────────────────────────────────▶
                  │              │  cache MISS → query DB
                  └──────────────┘             → store in cache
                                               → return value

    WRITE request → write to DB
                  → DELETE the cached entry  (invalidate, not update)

Why delete rather than update on write?
  Updating the cache on write is tempting but risky. If the write fails after
  you update the cache, you now have stale data in cache and correct data in
  the DB — a split-brain you won't notice until the TTL expires. Deleting on
  write means the next read just takes a fresh miss. Simpler and safer.

Trade-off: The first request after any write takes a DB hit (cold start).
  Under high traffic this is usually fine — that one request re-warms the cache
  for everyone after it.
"""

import time

import cache
import db

# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def get_product(session, product_id: int) -> dict | None:
    key = cache.product_key(product_id)
    raw = cache.get(key)

    if raw is not None:
        print(f"    CACHE HIT  {key!r}  (TTL={cache.ttl(key)}s remaining)")
        return cache.deserialise(raw)

    # Cache miss — go to the database
    print(f"    CACHE MISS {key!r}  → querying database...")
    product = session.get(db.Product, product_id)
    if product is None:
        return None

    # Populate the cache for the next caller
    serialised = cache.serialise(product)
    cache.setex(key, cache.PRODUCT_TTL, serialised)
    print(f"    CACHE SET  {key!r}  TTL={cache.PRODUCT_TTL}s")
    return cache.deserialise(serialised)


def update_price(session, product_id: int, new_price) -> None:
    """Write to DB, then invalidate the cache entry."""
    product = session.get(db.Product, product_id)
    if product is None:
        raise ValueError(f"Product {product_id} not found")

    old_price = product.price
    product.price = new_price
    session.commit()
    print(f"    DB WRITE   product {product_id}: price {old_price} → {new_price}")

    # Invalidate rather than update — see module docstring for why.
    key = cache.product_key(product_id)
    cache.delete(key)
    print(f"    CACHE DEL  {key!r}  (invalidated)")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    db.reset_schema()
    cache.flush_all()

    with db.get_session() as session:
        products = db.seed(session)
        keyboard = products[0]

    # ------------------------------------------------------------------
    print("\n=== 1. First access — cold cache ===")
    with db.get_session() as session:
        get_product(session, keyboard.id)

    # ------------------------------------------------------------------
    print("\n=== 2. Second access — warm cache (no DB query) ===")
    with db.get_session() as session:
        p = get_product(session, keyboard.id)
        print(f"    Returned: {p}")

    # ------------------------------------------------------------------
    print("\n=== 3. Third access — still warm ===")
    with db.get_session() as session:
        get_product(session, keyboard.id)
    cache.print_cache_state("After three reads", cache.product_key(keyboard.id))

    # ------------------------------------------------------------------
    print("\n=== 4. Price update — cache invalidated ===")
    with db.get_session() as session:
        update_price(session, keyboard.id, "89.99")
    cache.print_cache_state("After update", cache.product_key(keyboard.id))

    # ------------------------------------------------------------------
    print("\n=== 5. Next read after invalidation — cold again ===")
    with db.get_session() as session:
        p = get_product(session, keyboard.id)
        print(f"    Returned: {p}")
    cache.print_cache_state("Re-populated", cache.product_key(keyboard.id))

    # ------------------------------------------------------------------
    print(f"\n=== 6. TTL expiry — wait {cache.PRODUCT_TTL}s ===")
    print(f"    Waiting {cache.PRODUCT_TTL} seconds for cache entry to expire...")
    time.sleep(cache.PRODUCT_TTL + 1)
    cache.print_cache_state("After TTL expiry", cache.product_key(keyboard.id))

    print("\n=== 7. Access after TTL expiry — cold again ===")
    with db.get_session() as session:
        get_product(session, keyboard.id)


if __name__ == "__main__":
    main()
