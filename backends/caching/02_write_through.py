"""
Write-Through
==============
Every write goes to BOTH the database and the cache in the same operation.
The cache is never stale immediately after a write.

    WRITE request → write to DB
                  → write to cache  (same data, same moment)
                  → return

    READ request  → always hits cache (it was populated on the last write)
                  → falls back to DB only if the cache is cold at startup

Compare with cache-aside:
  Cache-aside populates the cache lazily (on the first read after a miss).
  Write-through populates the cache eagerly (on every write).

Advantage:
  Reads are always fast after the first write. No cold-start penalty per user.

Disadvantage:
  Every write is slightly slower because it must also write to Redis.
  If you write data that is never read, you've cached it for nothing.
  Cache and DB writes aren't atomic — a crash between the two leaves them
  out of sync. (Mitigated in practice by idempotent retries or short TTLs.)

When to use:
  Data with a high read-to-write ratio where you want zero cold-start latency.
  User profiles, product details, configuration.
"""

import cache
import db

# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def create_product(session, name: str, price, stock: int) -> db.Product:
    product = db.Product(name=name, price=price, stock=stock)
    session.add(product)
    session.commit()
    session.refresh(product)
    print(f"    DB INSERT   product {product.id}: {product.name!r}")

    # Write-through: populate cache immediately, not lazily
    key = cache.product_key(product.id)
    cache.setex(key, cache.PRODUCT_TTL, cache.serialise(product))
    print(f"    CACHE SET   {key!r}  TTL={cache.PRODUCT_TTL}s")

    return product


def update_product(session, product_id: int, **fields) -> db.Product:
    """
    Update any subset of fields. Uses a Redis pipeline so the DB write and
    cache write are sent as a single round-trip.
    """
    product = session.get(db.Product, product_id)
    if product is None:
        raise ValueError(f"Product {product_id} not found")

    for field, value in fields.items():
        setattr(product, field, value)
    session.commit()
    session.refresh(product)
    print(f"    DB UPDATE   product {product_id}: {fields}")

    # Pipeline: queue SET and EXPIRE together, send in one round-trip
    key = cache.product_key(product_id)
    pipe = cache.pipeline()
    pipe.set(key, cache.serialise(product))
    pipe.expire(key, cache.PRODUCT_TTL)
    pipe.execute()
    print(f"    CACHE SET   {key!r}  (pipeline, TTL={cache.PRODUCT_TTL}s)")

    return product


def get_product(session, product_id: int) -> dict:
    """Read — cache first, DB fallback (standard cache-aside read side)."""
    key = cache.product_key(product_id)
    raw = cache.get(key)
    if raw is not None:
        print(f"    CACHE HIT   {key!r}")
        return cache.deserialise(raw)

    print(f"    CACHE MISS  {key!r}  → DB fallback")
    product = session.get(db.Product, product_id)
    if product:
        cache.setex(key, cache.PRODUCT_TTL, cache.serialise(product))
    return cache.deserialise(cache.serialise(product)) if product else None


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    db.reset_schema()
    cache.flush_all()

    with db.get_session() as session:

        # ------------------------------------------------------------------
        print("\n=== 1. Create product — DB + cache written together ===")
        keyboard = create_product(session, "Mechanical Keyboard", "99.99", 50)

        # ------------------------------------------------------------------
        print("\n=== 2. Read immediately — cache is already warm ===")
        # Write-through means the first read is always a hit (no cold start)
        p = get_product(session, keyboard.id)
        print(f"    Returned:  {p}")

        # ------------------------------------------------------------------
        print("\n=== 3. Update price — cache updated in same operation ===")
        update_product(session, keyboard.id, price="89.99")

        # ------------------------------------------------------------------
        print("\n=== 4. Read after update — still a cache hit, fresh value ===")
        p = get_product(session, keyboard.id)
        print(f"    Returned:  {p}")
        cache.print_cache_state("Cache after update", cache.product_key(keyboard.id))

        # ------------------------------------------------------------------
        print("\n=== 5. Two fields updated in one call ===")
        update_product(session, keyboard.id, price="79.99", stock=45)
        p = get_product(session, keyboard.id)
        print(f"    Returned:  {p}")

        # ------------------------------------------------------------------
        print("\n=== 6. Cache-aside fallback (simulate cold start) ===")
        # Delete the cache entry to simulate startup with a warm DB but cold cache
        cache.delete(cache.product_key(keyboard.id))
        print(f"    Manually deleted {cache.product_key(keyboard.id)!r}")
        p = get_product(session, keyboard.id)  # triggers DB fallback
        print(f"    Returned:  {p}")


if __name__ == "__main__":
    main()
