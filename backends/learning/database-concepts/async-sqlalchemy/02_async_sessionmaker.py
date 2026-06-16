"""
async_sessionmaker and the expire_on_commit Trap
=================================================
async_sessionmaker is a factory that creates AsyncSession objects bound to
a specific engine. You call it once at module level, then call the factory
to get a new session wherever you need one.

Why a factory instead of creating sessions directly?
  - Consistent configuration (expire_on_commit, class_, etc.) in one place.
  - Composable: you can pass the factory into functions that don't need to
    know which database they're talking to.

The most important setting: expire_on_commit
────────────────────────────────────────────
After session.commit(), SQLAlchemy marks every loaded ORM object as "expired".
The intent is to ensure the next access reflects the latest DB state.

In SYNC SQLAlchemy, accessing an expired attribute transparently fires a new
SELECT — so the object stays usable after commit as long as the session is open.

In ASYNC SQLAlchemy, the same automatic refresh cannot happen outside of
an explicitly awaited call. If the session is closed (you've exited the
`async with` block) and you access an expired attribute, SQLAlchemy tries to
do a synchronous DB call and raises:

    sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called

Setting expire_on_commit=False prevents attributes from being expired on commit.
The object retains whatever values it had at commit time — safe to access after
the session closes, at the cost of potentially serving slightly stale data if
the DB is updated by someone else between your commit and your next read.

The default db.AsyncSessionFactory already sets expire_on_commit=False.
This demo creates a second factory with expire_on_commit=True to show
what breaks.
"""

import asyncio

from sqlalchemy.exc import MissingGreenlet
from sqlalchemy.ext.asyncio import async_sessionmaker

import db
from db import Product


# ---------------------------------------------------------------------------
# Demo 1: The trap — expire_on_commit=True, attribute access after session close
# ---------------------------------------------------------------------------

async def demo_expire_trap(product_id: int) -> None:
    print("\n=== 1. expire_on_commit=True — the trap ===")
    print("""
  Create a session factory with expire_on_commit=True (sync ORM default).
  Commit inside the session, then try to access the object after session closes.
""")
    unsafe_factory = async_sessionmaker(db.engine, expire_on_commit=True)

    product_ref = None
    async with unsafe_factory() as session:
        product_ref = await session.get(Product, product_id)
        await session.commit()
        # Attributes are now expired. Inside the session they can still be
        # refreshed by the async machinery if you await the right call — but
        # accessing them directly here works only by chance (the value is
        # cached on the Python object until the event loop yields).
        print(f"    Inside session after commit: id={product_ref.id}  name={product_ref.name!r}")

    # Session is now CLOSED. Accessing any expired column raises MissingGreenlet.
    print("    Session closed. Accessing product_ref.name...")
    try:
        _ = product_ref.name
        print("    (no error — attribute was not expired yet)")
    except MissingGreenlet as e:
        print(f"    MissingGreenlet: {e}")
    except Exception as e:
        print(f"    {type(e).__name__}: {e}")


# ---------------------------------------------------------------------------
# Demo 2: The fix — expire_on_commit=False
# ---------------------------------------------------------------------------

async def demo_expire_safe(product_id: int) -> None:
    print("\n=== 2. expire_on_commit=False — the safe pattern ===")
    print("""
  expire_on_commit=False means commit does NOT expire attributes.
  The object is safe to pass out of the session context.
""")
    product_ref = None
    async with db.get_session() as session:   # uses expire_on_commit=False
        product_ref = await session.get(Product, product_id)
        await session.commit()

    # Session is closed, but attributes are not expired.
    print(f"    Outside session: {product_ref}")


# ---------------------------------------------------------------------------
# Demo 3: session.refresh() — explicit reload
# ---------------------------------------------------------------------------

async def demo_refresh(product_id: int) -> None:
    print("\n=== 3. session.refresh() — explicit reload ===")
    print("""
  When you need to know the DB has given you the absolute latest values
  (e.g. server defaults, auto-incremented columns, trigger-set timestamps),
  call await session.refresh(obj). It fires a SELECT regardless of expiry state.
""")
    async with db.get_session() as session:
        product = await session.get(Product, product_id)
        print(f"    Before update: stock={product.stock}")

        # Simulate another process updating the stock directly in DB
        from sqlalchemy import update
        await session.execute(
            update(Product).where(Product.id == product_id).values(stock=99)
        )
        await session.commit()

        # Without refresh, the Python object still shows the old value
        print(f"    After commit (stale): stock={product.stock}")

        # Refresh forces a SELECT, giving us the current DB value
        await session.refresh(product)
        print(f"    After refresh:        stock={product.stock}")


# ---------------------------------------------------------------------------
# Demo 4: Identity map — session.get() doesn't re-query within a session
# ---------------------------------------------------------------------------

async def demo_identity_map(product_id: int) -> None:
    print("\n=== 4. Identity map — session.get() avoids duplicate queries ===")
    print("""
  Within a single session, SQLAlchemy maintains an identity map: a dict of
  all objects loaded in this session keyed by (type, primary key).
  Calling session.get() for the same PK a second time returns the cached
  object — no SQL round-trip.

  execute(select(...)) always hits the DB.
  session.get()        uses the identity map when possible.
""")
    async with db.get_session() as session:
        print(f"    First  session.get({product_id}) — will query DB:")
        p1 = await session.get(Product, product_id)
        print(f"      {p1}")

        print(f"    Second session.get({product_id}) — will use identity map (no SQL):")
        p2 = await session.get(Product, product_id)
        print(f"      {p2}")
        print(f"    p1 is p2: {p1 is p2}  (same Python object)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    await db.reset_schema()
    async with db.get_session() as session:
        products = await db.seed(session)
        keyboard = products[0]

    await demo_expire_trap(keyboard.id)
    await demo_expire_safe(keyboard.id)
    await demo_refresh(keyboard.id)
    await demo_identity_map(keyboard.id)

    await db.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
