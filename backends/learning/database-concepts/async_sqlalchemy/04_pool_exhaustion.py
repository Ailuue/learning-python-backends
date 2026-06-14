"""
Pool Exhaustion
================
Pool exhaustion happens when every connection in the pool (pool_size +
max_overflow) is in use and a new request needs one. The caller waits up to
pool_timeout seconds, then gets:

    sqlalchemy.exc.TimeoutError:
      QueuePool limit of size 3 overflow 0 reached,
      connection timed out, timeout 2.00 (Background on this error at: ...)

This is one of the most common production database errors. It shows up as:
  - 500 errors after a sudden traffic spike
  - Latency spikes at exactly pool_timeout seconds
  - "connection timed out" in logs alongside normal DB latency

Root causes:
  1. pool_size is too small for the concurrency level
  2. Requests hold connections longer than necessary (N+1 queries, long loops
     inside a session, or forgetting to close the session promptly)
  3. A slow query backs up and connections pile up waiting for it to finish
  4. A downstream dependency (external API, slow third-party call) is awaited
     INSIDE a session context, holding the connection the whole time

The fix is usually not just "make pool_size bigger" — that treats the symptom.
Better approaches:
  - Shorten how long you hold connections (commit early, close sessions ASAP)
  - Move non-DB work outside the session context
  - Use a server-side connection pooler like PgBouncer so many app instances
    can share a smaller number of actual DB connections

This script spawns 10 concurrent tasks that each hold a connection for 3s,
against a pool of only 3. You'll see exactly 3 succeed and 7 time out.
Then it repeats with a pool big enough for all tasks.
"""

import asyncio

from sqlalchemy import text
from sqlalchemy.exc import TimeoutError as PoolTimeout
from sqlalchemy.ext.asyncio import async_sessionmaker

import db


HOLD_SECONDS   = 3.0   # how long each task holds its connection
POOL_TIMEOUT   = 2.0   # how long a task waits before giving up
N_TASKS        = 10    # concurrent requests


# ---------------------------------------------------------------------------
# Task: grab a connection, hold it, release it
# ---------------------------------------------------------------------------

async def do_work(factory, task_id: int) -> str:
    try:
        async with factory() as session:
            await session.execute(text("SELECT 1"))      # checks out connection
            await asyncio.sleep(HOLD_SECONDS)            # simulates slow query
        return f"task-{task_id:02d}  OK"
    except PoolTimeout:
        return f"task-{task_id:02d}  TIMEOUT (waited {POOL_TIMEOUT}s, no connection available)"


# ---------------------------------------------------------------------------
# Demo 1: Pool too small → exhaustion
# ---------------------------------------------------------------------------

async def demo_exhaustion() -> None:
    print("\n=== 1. Pool exhaustion ===")
    print(f"""
  pool_size={3}, max_overflow=0  →  max {3} simultaneous connections
  {N_TASKS} tasks, each holding a connection for {HOLD_SECONDS}s
  pool_timeout={POOL_TIMEOUT}s   →  tasks wait at most {POOL_TIMEOUT}s before failing
""")

    eng = db.make_engine(pool_size=3, max_overflow=0, pool_timeout=POOL_TIMEOUT)
    factory = async_sessionmaker(eng, expire_on_commit=False)

    results = await asyncio.gather(
        *[do_work(factory, i) for i in range(N_TASKS)]
    )

    ok      = [r for r in results if "OK"      in r]
    timeout = [r for r in results if "TIMEOUT" in r]

    for r in sorted(results):
        print(f"    {r}")

    print(f"""
  {len(ok)} tasks succeeded  (got a connection from the pool of 3)
  {len(timeout)} tasks timed out  (pool exhausted for {POOL_TIMEOUT}s straight)
""")
    await eng.dispose()


# ---------------------------------------------------------------------------
# Demo 2: The naive "fix" — just make the pool bigger
# ---------------------------------------------------------------------------

async def demo_bigger_pool() -> None:
    print("=== 2. Bigger pool — the easy fix ===")
    print(f"""
  Raise pool_size to {N_TASKS} so every task gets a connection immediately.
  This works — but it means {N_TASKS} open PostgreSQL connections at all times.
  PostgreSQL allocates ~5-10MB of shared memory per connection. At scale this
  adds up fast. The real fix is usually to hold connections for less time.
""")

    eng = db.make_engine(pool_size=N_TASKS, max_overflow=0, pool_timeout=POOL_TIMEOUT)
    factory = async_sessionmaker(eng, expire_on_commit=False)

    results = await asyncio.gather(
        *[do_work(factory, i) for i in range(N_TASKS)]
    )

    ok = [r for r in results if "OK" in r]
    print(f"  {len(ok)}/{N_TASKS} tasks succeeded (no exhaustion)\n")
    await eng.dispose()


# ---------------------------------------------------------------------------
# Demo 3: The better fix — hold connections for less time
# ---------------------------------------------------------------------------

async def work_outside_session(task_id: int) -> str:
    """
    Correct pattern: do non-DB work OUTSIDE the session context.
    The connection is held only during the actual query, not during the sleep.
    """
    try:
        # Step 1: fetch from DB (holds connection briefly)
        async with db.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()

        # Step 2: non-DB processing happens outside the session context.
        # The connection was returned to the pool after the `async with` block above.
        await asyncio.sleep(HOLD_SECONDS)   # simulate slow post-processing

        return f"task-{task_id:02d}  OK (connection held only during query)"
    except PoolTimeout:
        return f"task-{task_id:02d}  TIMEOUT"


async def demo_short_hold() -> None:
    print("=== 3. Better fix — release connections quickly ===")
    print(f"""
  Same {N_TASKS} concurrent tasks, same {HOLD_SECONDS}s of work — but now the slow part
  happens OUTSIDE the session context. The connection is returned to the pool
  as soon as the query finishes, before the sleep begins.

  With pool_size={3}: the {N_TASKS} tasks share 3 connections without exhaustion
  because each connection is only held for milliseconds per task.
""")

    eng = db.make_engine(pool_size=3, max_overflow=0, pool_timeout=POOL_TIMEOUT)

    results = await asyncio.gather(
        *[work_outside_session(i) for i in range(N_TASKS)]
    )

    ok      = [r for r in results if "OK"      in r]
    timeout = [r for r in results if "TIMEOUT" in r]

    print(f"  {len(ok)} succeeded, {len(timeout)} timed out  (pool_size=3, same small pool)\n")
    await eng.dispose()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    await demo_exhaustion()
    await demo_bigger_pool()
    await demo_short_hold()

    print("""
  Key takeaways
  ─────────────
  1. Pool exhaustion is almost always a connection hold time problem, not a
     pool_size problem. Profile your sessions before reaching for a bigger pool.

  2. Never hold a connection while waiting on something that isn't the DB:
     external HTTP calls, file I/O, CPU work, asyncio.sleep. Fetch what you
     need, close the session, THEN do the other work.

  3. For truly high-concurrency workloads, use PgBouncer in transaction mode:
     it multiplexes thousands of app connections onto a few DB connections,
     so you never need pool_size > a few dozen even at massive scale.
""")


if __name__ == "__main__":
    asyncio.run(main())
