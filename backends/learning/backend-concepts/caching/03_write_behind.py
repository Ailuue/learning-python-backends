"""
Write-Behind (Write-Back)
==========================
Writes go to the cache immediately and return. A separate flush step
(typically a background worker or cron job) drains the pending queue and
writes to the database in batches.

    WRITE request → write to cache
                  → push job onto pending queue
                  → return immediately  ← caller doesn't wait for DB

    FLUSH worker  → read pending queue
                  → batch-write to DB
                  → clear queue

Advantage:
  Write latency is extremely low — the caller only waits for Redis, not
  the database. Under bursty write load, the queue absorbs spikes.
  Multiple updates to the same key before a flush collapse into one DB write.

Disadvantage:
  If the Redis node crashes before the flush, pending writes are lost.
  The DB and cache are intentionally out of sync between flushes.
  Flush logic must be idempotent and handle partial failures.

When to use:
  High-frequency writes where some data loss is tolerable: analytics counters,
  view counts, "last seen" timestamps. NOT for financial transactions.
"""

import json

import cache
import db
from db import Product

PENDING_KEY = cache.pending_writes_key()


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def update_stock(session, product_id: int, new_stock: int) -> None:
    """
    Write to cache immediately. Queue a pending flush job for the DB.
    The caller returns before the database is touched.
    """
    key = cache.product_key(product_id)

    # Update cache — the caller sees the new value instantly
    raw = cache.get(key)
    if raw:
        data = cache.deserialise(raw)
        data["stock"] = new_stock
        cache.setex(key, cache.PRODUCT_TTL, json.dumps(data))
        print(f"    CACHE SET  {key!r}  stock → {new_stock}")
    else:
        # If cache is cold we still queue the write; the DB gets updated on flush
        print(f"    CACHE COLD {key!r}  (queuing write anyway)")

    # Push a pending-write descriptor onto the queue
    job = json.dumps({"product_id": product_id, "stock": new_stock})
    cache.rpush(PENDING_KEY, job)
    print(f"    QUEUE PUSH pending:writes  ({cache.llen(PENDING_KEY)} items in queue)")


def flush_pending_writes(session) -> int:
    """
    Drain the entire pending queue and apply all writes to the database.
    Returns the number of writes flushed.

    In production this would run on a schedule (e.g. every 5 seconds).
    Multiple updates to the same product_id are coalesced: only the last
    value in the batch is written, saving DB round-trips.
    """
    length = cache.llen(PENDING_KEY)
    if length == 0:
        print("    FLUSH      nothing to flush")
        return 0

    # Read entire queue and atomically trim it
    raw_jobs = cache.lrange(PENDING_KEY, 0, -1)
    cache.ltrim(PENDING_KEY, length, -1)  # remove the items we just read

    # Coalesce: last update for each product_id wins
    coalesced: dict[int, dict] = {}
    for raw in raw_jobs:
        job = json.loads(raw)
        coalesced[job["product_id"]] = job

    print(f"    FLUSH      {length} queued writes → {len(coalesced)} unique products")

    for product_id, job in coalesced.items():
        product = session.get(Product, product_id)
        if product is not None:
            old_stock = product.stock
            product.stock = job["stock"]
            print(f"    DB UPDATE  product {product_id}: stock {old_stock} → {product.stock}")

    session.commit()
    print("    FLUSH      committed")
    return len(coalesced)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    db.reset_schema()
    cache.flush_all()

    with db.get_session() as session:
        products = db.seed(session)
        hub = products[1]  # USB-C Hub, stock=130

    # Pre-populate cache so cache-side updates work
    with db.get_session() as session:
        hub = session.get(Product, hub.id)
        assert hub is not None, "seeded product disappeared"
        cache.setex(cache.product_key(hub.id), cache.PRODUCT_TTL, cache.serialise(hub))

    # ------------------------------------------------------------------
    print("\n=== 1. Burst of stock updates — fast, no DB writes yet ===")
    with db.get_session() as session:
        for new_stock in [129, 128, 127, 126, 125]:
            update_stock(session, hub.id, new_stock)

    print("\n  DB right now (before flush):")
    with db.get_session() as session:
        current = session.get(Product, hub.id)
        assert current is not None
        print(f"    DB stock = {current.stock}  (still 130 — writes are queued)")

    cache_val = cache.get(cache.product_key(hub.id))
    if cache_val:
        print(f"    Cache stock = {cache.deserialise(cache_val)['stock']}  (already updated to 125)")

    # ------------------------------------------------------------------
    print("\n=== 2. Flush pending writes to DB ===")
    with db.get_session() as session:
        flush_pending_writes(session)

    # ------------------------------------------------------------------
    print("\n=== 3. Verify DB now matches cache ===")
    with db.get_session() as session:
        current = session.get(Product, hub.id)
        assert current is not None
        print(f"\n    DB stock    = {current.stock}  (expected 125)")
    cache_val = cache.get(cache.product_key(hub.id))
    if cache_val:
        print(f"    Cache stock = {cache.deserialise(cache_val)['stock']}")

    # ------------------------------------------------------------------
    print("\n=== 4. Updates to multiple products ===")
    with db.get_session() as session:
        products = db.seed(session)  # fresh set
        for p in products:
            cache.setex(cache.product_key(p.id), cache.PRODUCT_TTL, cache.serialise(p))

    with db.get_session() as session:
        for p in products:
            update_stock(session, p.id, p.stock - 5)

    print("\n  Flush all:")
    with db.get_session() as session:
        flush_pending_writes(session)
    db.print_products(db.get_session().__enter__(), "DB after flush")

    # ------------------------------------------------------------------
    print("\n=== 5. The risk: crash before flush ===")
    print("""
  If Redis crashes after step 1 but before step 2:
    - The cache is gone (or returns stale data)
    - The DB still has stock=130
    - The 5 write operations are lost

  This is the fundamental trade-off of write-behind.
  Acceptable for: view counts, "last active" timestamps, metrics.
  NOT acceptable for: inventory changes, financial records, orders.
""")


if __name__ == "__main__":
    main()
