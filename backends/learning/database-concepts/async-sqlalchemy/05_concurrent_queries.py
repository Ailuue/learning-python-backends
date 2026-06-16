"""
Concurrent Queries — The Payoff
================================
Everything so far has been about avoiding problems. This script shows what
you actually gain from async: running independent queries in parallel.

In a sync web handler you write:
    product  = db.get_product(id)      # 50ms
    reviews  = db.get_reviews(id)      # 50ms
    total: 100ms — you waited for each query before starting the next.

With async:
    product, reviews = await asyncio.gather(
        get_product(id),
        get_reviews(id),
    )
    total: ~50ms — both queries run simultaneously.

asyncio.gather() takes a list of coroutines and runs them concurrently on
the same event loop. Each coroutine can use its own session (its own connection
from the pool) so they don't block each other.

When does async NOT help?
─────────────────────────
- Queries that depend on each other (you must load user before loading their orders)
- CPU-bound work (async only parallelises I/O; heavy Python computation still
  blocks the event loop and needs multiprocessing)
- Queries that are already sub-millisecond (the gather overhead isn't worth it)
- A single request on an otherwise idle server (sync and async perform the same)

Async pays off at the system level: many concurrent requests each doing several
independent I/O calls. That's exactly the profile of a REST API.
"""

import asyncio
import time

from sqlalchemy import text

import db
from db import Product

# pg_sleep creates real database latency so the timing numbers are meaningful.
QUERY_LATENCY_S = 0.05   # 50ms simulated slow query


# ---------------------------------------------------------------------------
# A "slow" product fetch — simulates a query that takes QUERY_LATENCY_S
# ---------------------------------------------------------------------------

async def fetch_product(product_id: int) -> dict:
    async with db.get_session() as session:
        await session.execute(text(f"SELECT pg_sleep({QUERY_LATENCY_S})"))
        product = await session.get(Product, product_id)
        return {"id": product.id, "name": product.name, "price": str(product.price)}


# ---------------------------------------------------------------------------
# Demo 1: Sequential — one after the other
# ---------------------------------------------------------------------------

async def demo_sequential(product_ids: list[int]) -> float:
    print(f"\n=== 1. Sequential — {len(product_ids)} queries, one at a time ===")

    start = time.perf_counter()
    results = [await fetch_product(pid) for pid in product_ids]
    elapsed = time.perf_counter() - start

    print(f"  Time: {elapsed:.2f}s  (expected ~{len(product_ids) * QUERY_LATENCY_S:.2f}s)")
    print(f"  Results: {[r['name'] for r in results]}")
    return elapsed


# ---------------------------------------------------------------------------
# Demo 2: Concurrent — all at once with asyncio.gather
# ---------------------------------------------------------------------------

async def demo_concurrent(product_ids: list[int]) -> float:
    print(f"\n=== 2. Concurrent — {len(product_ids)} queries via asyncio.gather ===")

    start = time.perf_counter()
    results = await asyncio.gather(*[fetch_product(pid) for pid in product_ids])
    elapsed = time.perf_counter() - start

    print(f"  Time: {elapsed:.2f}s  (expected ~{QUERY_LATENCY_S:.2f}s)")
    print(f"  Results: {[r['name'] for r in results]}")
    return elapsed


# ---------------------------------------------------------------------------
# Demo 3: Real-world pattern — load a "detail page" with multiple resources
# ---------------------------------------------------------------------------

async def get_product_detail(product_id: int) -> dict:
    """
    Simulates a detail-page endpoint that needs three independent pieces of data.
    In a real app these might be: the product, its reviews, and related products.

    The point: these queries don't depend on each other, so there's no reason to
    run them sequentially. asyncio.gather fires them concurrently on separate
    connections and waits for all three, so the total time is the slowest query
    rather than the sum of all three.
    """
    # These three calls are independent — fire them all at once.
    product_data, stock_data, price_data = await asyncio.gather(
        _fetch_with_latency(f"product {product_id} details", 0.04),
        _fetch_with_latency("stock levels",                  0.06),
        _fetch_with_latency("price history",                 0.05),
    )

    return {
        "product":  product_data,
        "stock":    stock_data,
        "price":    price_data,
    }


async def _fetch_with_latency(label: str, seconds: float) -> str:
    async with db.get_session() as session:
        await session.execute(text(f"SELECT pg_sleep({seconds})"))
    return f"{label} loaded"


async def demo_detail_page() -> None:
    print("\n=== 3. Detail-page pattern — three independent fetches in parallel ===")
    print("""
  Loading product + stock + price history sequentially would take 0.04 + 0.06 + 0.05 = 0.15s.
  Loading them concurrently takes ~0.06s (the slowest of the three).
""")

    async with db.get_session() as session:
        products = await db.seed(session)

    start = time.perf_counter()
    detail = await get_product_detail(products[0].id)
    elapsed = time.perf_counter() - start

    for k, v in detail.items():
        print(f"  {k}: {v}")
    print(f"\n  Total: {elapsed:.2f}s  (expected ~0.06s — limited by slowest call)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    await db.reset_schema()
    async with db.get_session() as session:
        products = await db.seed(session)

    # Repeat each product ID 3 times = 9 queries total
    ids = [p.id for p in products] * 3

    seq_time = await demo_sequential(ids)
    con_time = await demo_concurrent(ids)

    print(f"\n  Speedup: {seq_time / con_time:.1f}x  "
          f"({seq_time:.2f}s sequential → {con_time:.2f}s concurrent)")

    await demo_detail_page()

    await db.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
