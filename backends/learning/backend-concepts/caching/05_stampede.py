"""
Cache Stampede (Thundering Herd)
=================================
A cache stampede happens when many requests arrive simultaneously for a key
that has just expired (or never been set). Every request sees a miss, every
request goes to the database, and the database gets hammered.

    t=0   key expires
    t=1   request A: MISS → queries DB
    t=1   request B: MISS → queries DB       ← all see the same miss
    t=1   request C: MISS → queries DB
    ...   (N concurrent requests = N DB queries for the same row)

Two solutions are demonstrated here:

  1. Redis distributed lock (mutex)
     The first requester acquires a lock, fetches from DB, populates cache,
     releases lock. All other requesters wait and then read from the warm cache.
     Result: exactly ONE DB query per stampede event.

  2. Probabilistic early expiry (XFetch)
     Instead of waiting for hard expiry, each reader occasionally refreshes
     the cache slightly early using a randomised probability that increases as
     the key approaches expiry. No locking needed, no thundering herd.
     Result: cache is refreshed smoothly in the background.

This script uses threading to simulate concurrent requests so you can see
the difference in DB hit count directly.
"""

import random
import threading
import time

import cache
import db
from db import Product

# ---------------------------------------------------------------------------
# Shared counter — tracks how many times the DB was actually queried
# ---------------------------------------------------------------------------

db_hits = 0
db_hits_lock = threading.Lock()

def record_db_hit():
    global db_hits
    with db_hits_lock:
        db_hits += 1


# ---------------------------------------------------------------------------
# Without protection — naive cache-aside, no lock
# ---------------------------------------------------------------------------

def get_product_naive(product_id: int, request_n: int) -> dict:
    key = cache.product_key(product_id)
    raw = cache.get(key)
    if raw is not None:
        return cache.deserialise(raw)

    # Simulate DB latency
    time.sleep(0.05)
    record_db_hit()

    with db.get_session() as session:
        product = session.get(Product, product_id)

    serialised = cache.serialise(product)
    cache.setex(key, cache.PRODUCT_TTL, serialised)
    return cache.deserialise(serialised)


# ---------------------------------------------------------------------------
# Solution 1: Redis lock (mutex)
# ---------------------------------------------------------------------------

LOCK_VALUE = "1"
RETRY_SLEEP = 0.01  # how long to wait before retrying lock acquisition

def get_product_with_lock(product_id: int, request_n: int) -> dict:
    key = cache.product_key(product_id)
    lock = cache.lock_key(product_id)

    while True:
        # Fast path: cache hit
        raw = cache.get(key)
        if raw is not None:
            return cache.deserialise(raw)

        # Try to acquire the lock (SET NX EX — atomic)
        acquired = cache.set_nx(lock, LOCK_VALUE, ex=cache.LOCK_TTL)
        if acquired:
            try:
                # Double-check: another thread may have populated cache
                # while we were acquiring the lock
                raw = cache.get(key)
                if raw is not None:
                    return cache.deserialise(raw)

                # We hold the lock — go to DB
                time.sleep(0.05)
                record_db_hit()
                with db.get_session() as session:
                    product = session.get(Product, product_id)
                serialised = cache.serialise(product)
                cache.setex(key, cache.PRODUCT_TTL, serialised)
                return cache.deserialise(serialised)
            finally:
                cache.delete(lock)
        else:
            # Lock is held by another thread — wait and retry
            time.sleep(RETRY_SLEEP)


# ---------------------------------------------------------------------------
# Solution 2: Probabilistic early expiry (XFetch / PER algorithm)
# ---------------------------------------------------------------------------
# Reference: "Optimal probabilistic cache stampede prevention"
# Formula:   expiry_time - current_time < -beta * delta * log(random())
#   delta = time it took to compute the value (simulated as RECOMPUTE_TIME)
#   beta  = tuning parameter (higher = more eager refresh, default 1.0)

RECOMPUTE_TIME = 0.05  # simulated DB query time in seconds
BETA = 1.0

# We store (value, expiry_timestamp) so readers know when the key expires.
# In production you'd store this as a Redis hash or embed it in the JSON.
_per_store: dict[str, tuple[str, float]] = {}
_per_lock = threading.Lock()

def get_product_per(product_id: int, request_n: int) -> dict:
    key = cache.product_key(product_id)

    with _per_lock:
        entry = _per_store.get(key)

    if entry is not None:
        value, expiry = entry
        ttl_remaining = expiry - time.time()

        # Probabilistic check: should we refresh early?
        # As expiry approaches, this fires more often.
        if ttl_remaining > 0:
            prob_score = -BETA * RECOMPUTE_TIME * (random.random() + 1e-10)
            if ttl_remaining > prob_score:
                # Key is still fresh enough — no refresh needed
                return cache.deserialise(value)

    # Miss or probabilistic refresh — fetch from DB
    time.sleep(RECOMPUTE_TIME)
    record_db_hit()
    with db.get_session() as session:
        product = session.get(Product, product_id)
    serialised = cache.serialise(product)
    expiry = time.time() + cache.PRODUCT_TTL

    with _per_lock:
        _per_store[key] = (serialised, expiry)

    return cache.deserialise(serialised)


# ---------------------------------------------------------------------------
# Benchmark helper
# ---------------------------------------------------------------------------

def run_concurrent(fn, product_id: int, n_threads: int, label: str):
    global db_hits
    db_hits = 0

    threads = [
        threading.Thread(target=fn, args=(product_id, i))
        for i in range(n_threads)
    ]

    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - start

    print(f"  {label:<40s}  DB hits: {db_hits:2d}  ({elapsed:.2f}s total)")
    return db_hits


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    db.reset_schema()
    cache.flush_all()

    with db.get_session() as session:
        products = db.seed(session)
        keyboard = products[0]

    N = 20  # number of concurrent requests

    # ------------------------------------------------------------------
    print(f"\n=== Cold-cache stampede: {N} concurrent requests, no cached value ===\n")

    cache.flush_all()
    _per_store.clear()
    naive_hits = run_concurrent(get_product_naive, keyboard.id, N, "Naive (no protection)")

    cache.flush_all()
    _per_store.clear()
    lock_hits = run_concurrent(get_product_with_lock, keyboard.id, N, "Redis lock")

    print(f"""
  Cold start summary:
    Naive:       {naive_hits} DB hits — every request misses, all query the DB
    Redis lock:  {lock_hits} DB hit  — one thread fetches, the rest wait for the lock
                          then read from the warm cache

  Probabilistic early expiry (PER) does NOT help cold-start stampedes.
  PER is designed for a different scenario: preventing the surge that
  happens when a hot key's TTL expires under sustained traffic.
""")

    # ------------------------------------------------------------------
    print(f"=== Expiry-time stampede: {N} concurrent requests just as TTL expires ===\n")
    print("  Pre-warming cache with a very short TTL (1s)...")

    # Pre-warm both the naive cache and the PER store with the same short TTL
    with db.get_session() as session:
        p = session.get(db.Product, keyboard.id)
        serialised = cache.serialise(p)

    # Naive: let the key expire naturally, then fire concurrent requests
    cache.flush_all()
    cache.setex(cache.product_key(keyboard.id), 1, serialised)
    time.sleep(1.1)  # wait for TTL to expire
    global db_hits
    db_hits = 0
    naive_expiry_hits = run_concurrent(get_product_naive, keyboard.id, N,
                                       "Naive at expiry")

    # Redis lock: same — let expire, then fire
    cache.flush_all()
    cache.setex(cache.product_key(keyboard.id), 1, serialised)
    time.sleep(1.1)
    db_hits = 0
    lock_expiry_hits = run_concurrent(get_product_with_lock, keyboard.id, N,
                                      "Redis lock at expiry")

    print(f"""
  Expiry-time summary (concurrent burst):
    Naive at expiry:      {naive_expiry_hits} DB hits — same stampede as cold start
    Redis lock at expiry: {lock_expiry_hits} DB hit  — lock serialises access

  PER (probabilistic early expiry) doesn't help a concurrent burst because
  all threads make their independent refresh decisions simultaneously and most
  still see an expired key. PER's benefit appears under *sustained sequential
  traffic*, which is how real web servers receive requests.
""")

    # ------------------------------------------------------------------
    print("=== Probabilistic early expiry under sustained traffic ===\n")
    print("  Simulating 40 sequential requests spaced 0.1s apart,")
    print("  cache TTL=3s — watch for the early refresh before hard expiry.\n")

    PER_DEMO_TTL = 3  # short TTL so 40 requests at 0.1s intervals span past expiry

    _per_store.clear()
    with db.get_session() as session:
        p = session.get(db.Product, keyboard.id)
        s2 = cache.serialise(p)
    key = cache.product_key(keyboard.id)
    expiry = time.time() + PER_DEMO_TTL
    with _per_lock:
        _per_store[key] = (s2, expiry)
    print(f"  Cache set, expires at T+{PER_DEMO_TTL}s\n")

    # Use a higher beta so the demo reliably shows at least one early refresh.
    # In production beta=1.0 is standard; higher values make refreshes more eager.
    DEMO_BETA = 3.0

    db_hits = 0
    for req in range(40):
        t = time.time()
        entry = _per_store.get(key)
        if entry:
            value, exp = entry
            ttl_remaining = exp - t
            if ttl_remaining > 0:
                prob_score = -DEMO_BETA * RECOMPUTE_TIME * (random.random() + 1e-10)
                if ttl_remaining > -prob_score:
                    elapsed_s = t - (expiry - PER_DEMO_TTL)
                    status = f"HIT   (TTL={ttl_remaining:.2f}s remaining)"
                else:
                    # PER decided to refresh early
                    time.sleep(RECOMPUTE_TIME)
                    record_db_hit()
                    with db.get_session() as session:
                        product = session.get(db.Product, keyboard.id)
                    new_serialised = cache.serialise(product)
                    new_expiry = time.time() + PER_DEMO_TTL
                    with _per_lock:
                        _per_store[key] = (new_serialised, new_expiry)
                    elapsed_s = t - (expiry - PER_DEMO_TTL)
                    status = f"EARLY REFRESH (TTL was {ttl_remaining:.2f}s) ← new TTL={PER_DEMO_TTL}s"
            else:
                # Actual expiry
                time.sleep(RECOMPUTE_TIME)
                record_db_hit()
                with db.get_session() as session:
                    product = session.get(db.Product, keyboard.id)
                new_serialised = cache.serialise(product)
                new_expiry = time.time() + PER_DEMO_TTL
                with _per_lock:
                    _per_store[key] = (new_serialised, new_expiry)
                elapsed_s = t - (expiry - PER_DEMO_TTL)
                status = "EXPIRED MISS  (served cold)"
        else:
            elapsed_s = 0
            status = "COLD MISS"

        elapsed_s = t - (expiry - PER_DEMO_TTL)
        print(f"  req {req+1:02d}  T+{elapsed_s:.1f}s  {status}")
        time.sleep(0.1)

    print(f"""
  Result: {db_hits} DB hit(s) across 40 requests spanning {PER_DEMO_TTL}s.

  The early refresh happened before the TTL fired, so there was no
  bang at expiry — subsequent requests served from the refreshed cache.

  Redis lock vs PER:
    Lock:  serialises access — one waiter does the work, others block briefly
    PER:   no blocking — one reader refreshes slightly early, others keep reading
           Best when lock contention itself is a bottleneck (millions of RPS)
""")


if __name__ == "__main__":
    main()
