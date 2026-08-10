"""
Connection Pool Configuration
==============================
Opening a fresh TCP connection to PostgreSQL takes ~1–5ms — small per request,
but at 1 000 req/s that's 1–5 seconds of pure connection overhead per second.
A connection pool keeps a set of connections open and reuses them.

The five pool knobs
───────────────────
pool_size      The number of connections kept open and idle, ready to lend out.
               Default: 5. A good starting point is (2 × CPU cores) for CPU-
               bound apps, or higher for I/O-heavy ones.

max_overflow   Additional connections allowed above pool_size when all pool_size
               connections are in use. These are created on demand and closed
               when returned (not recycled). Default: 10.
               Max simultaneous connections = pool_size + max_overflow.

pool_timeout   How long (seconds) a caller waits for a free connection before
               raising sqlalchemy.exc.TimeoutError. Default: 30.
               See 04_pool_exhaustion.py for what that error looks like.

pool_recycle   Max connection age in seconds. After this time a connection is
               discarded and a fresh one opened on next use. Prevents silent
               failures from firewalls or the DB server closing idle connections.
               Default: -1 (no recycle). Common values: 1800–3600.

pool_pre_ping  If True, sends a lightweight "SELECT 1" before lending out a
               connection. If the ping fails (connection is dead), the pool
               discards that connection and tries the next one. Adds a tiny
               overhead per checkout but eliminates "connection closed" errors
               after a DB restart or network blip. Default: False.
               Use True in any production app.

This script creates a small pool and opens/closes sessions so you can watch
the pool state change in real time.
"""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

import db


# ---------------------------------------------------------------------------
# Helper: hold a connection for `seconds`, then release
# ---------------------------------------------------------------------------

async def hold_connection(factory, seconds: float, label: str) -> None:
    async with factory() as session:
        await session.execute(text("SELECT 1"))  # actually checks out connection
        await asyncio.sleep(seconds)
    # Connection returned to pool here (session.__aexit__)


# ---------------------------------------------------------------------------
# Demo 1: Watch pool state as sessions open and close
# ---------------------------------------------------------------------------

async def demo_pool_lifecycle() -> None:
    print("\n=== 1. Pool lifecycle — watching connections come and go ===")

    eng = db.make_engine(pool_size=3, max_overflow=2, pool_timeout=5.0)
    factory = async_sessionmaker(eng, expire_on_commit=False)
    await db.reset_schema(eng)

    db.print_pool_status(eng, "Start — no connections yet")

    # Open 3 sessions (fills pool_size)
    tasks = [
        asyncio.create_task(hold_connection(factory, seconds=1.0, label=f"sess-{i}"))
        for i in range(3)
    ]
    await asyncio.sleep(0.1)   # give tasks time to acquire their connections
    db.print_pool_status(eng, "3 sessions open — pool full")

    # Open 2 more (hits overflow)
    overflow_tasks = [
        asyncio.create_task(hold_connection(factory, seconds=0.5, label=f"overflow-{i}"))
        for i in range(2)
    ]
    await asyncio.sleep(0.1)
    db.print_pool_status(eng, "5 sessions open — 2 overflow connections in use")

    # Wait for overflow tasks to finish
    await asyncio.gather(*overflow_tasks)
    await asyncio.sleep(0.05)
    db.print_pool_status(eng, "Overflow tasks done — overflow connections discarded")

    # Wait for pool tasks to finish
    await asyncio.gather(*tasks)
    await asyncio.sleep(0.05)
    db.print_pool_status(eng, "All sessions closed — connections idle in pool")

    await eng.dispose()
    print("\n  dispose() closed all idle connections (call at app shutdown).")


# ---------------------------------------------------------------------------
# Demo 2: pool_pre_ping — detecting stale connections
# ---------------------------------------------------------------------------

async def demo_pre_ping() -> None:
    print("\n\n=== 2. pool_pre_ping ===")
    print("""
  With pool_pre_ping=True, SQLAlchemy runs "SELECT 1" before lending out each
  connection. If the DB server restarted (or a firewall closed the TCP session
  while the connection was idle), the ping fails, the dead connection is discarded,
  and a fresh one is opened transparently.

  Without pool_pre_ping, the caller gets the dead connection and sees:
    psycopg2.OperationalError: SSL connection has been closed unexpectedly
  or similar — a confusing error that only happens in production after idle periods.

  The overhead is one extra round-trip per checkout (~0.2ms on a LAN).
  Always enable it in production.
""")
    eng_with    = db.make_engine(pool_pre_ping=True)
    eng_without = db.make_engine(pool_pre_ping=False)
    print(f"  pool_pre_ping=True  → {eng_with.pool._pre_ping}")
    print(f"  pool_pre_ping=False → {eng_without.pool._pre_ping}")
    await eng_with.dispose()
    await eng_without.dispose()


# ---------------------------------------------------------------------------
# Demo 3: pool_recycle — preventing silent stale connections
# ---------------------------------------------------------------------------

async def demo_pool_recycle() -> None:
    print("\n\n=== 3. pool_recycle ===")
    print("""
  Many corporate firewalls and cloud load balancers silently close TCP connections
  idle for more than N minutes. PostgreSQL itself closes connections idle past
  tcp_keepalives_idle. Your pool doesn't know this happened.

  pool_recycle=1800 tells SQLAlchemy: "if this connection is more than 30 minutes
  old, discard it on next checkout and open a fresh one."

  This is a belt-and-suspenders complement to pool_pre_ping:
    - pool_pre_ping catches already-dead connections (reactive)
    - pool_recycle prevents using old connections (proactive)
""")
    eng = db.make_engine(pool_size=5, max_overflow=0, pool_recycle=1800)
    print(f"  pool_recycle setting: {eng.sync_engine.pool._recycle}s")
    await eng.dispose()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    await demo_pool_lifecycle()
    await demo_pre_ping()
    await demo_pool_recycle()


if __name__ == "__main__":
    asyncio.run(main())
