"""
Async SQLAlchemy Basics
========================
The sync SQLAlchemy you've used elsewhere uses psycopg2 under the hood.
psycopg2 is a C extension that blocks the thread while waiting for the database.
That's fine if each request gets its own thread, but in an async web server
(FastAPI, aiohttp) there is only one thread — blocking it stalls every request.

asyncpg is a pure-Python async PostgreSQL driver. Every network call is an
awaitable coroutine, so the event loop is free to handle other requests while
the DB is doing its work.

SQLAlchemy's async extension (sqlalchemy.ext.asyncio) wraps asyncpg and keeps
the familiar ORM API, with two main changes:
  - every session method that touches the DB must be awaited
  - use  select(Model).where(...)  instead of  session.query(Model).filter(...)
    (the legacy Query API does not support async)

The seven methods you'll use most:
  await session.get(Model, pk)           → fetch by primary key (identity map)
  await session.execute(select(...))     → run any SELECT statement
  result.scalar_one()                    → unwrap exactly one row
  result.scalars().all()                 → unwrap a list of rows
  session.add(obj)                       → stage INSERT / UPDATE (no await)
  await session.commit()                 → flush + commit transaction
  await session.refresh(obj)             → reload object from DB after commit
"""

import asyncio
from decimal import Decimal

from sqlalchemy import select

import db
from db import Product


# ---------------------------------------------------------------------------
# INSERT
# ---------------------------------------------------------------------------

async def demo_insert() -> list[Product]:
    print("\n=== 1. INSERT ===")
    async with db.get_session() as session:
        products = await db.seed(session)
        for p in products:
            print(f"    Inserted: {p}")
    return products


# ---------------------------------------------------------------------------
# SELECT — two styles
# ---------------------------------------------------------------------------

async def demo_select(product_id: int) -> None:
    print("\n=== 2. SELECT by primary key — session.get() ===")
    print("""
  session.get() checks the session's identity map first (no SQL if the object
  is already loaded in this session), then falls back to a SELECT.
""")
    async with db.get_session() as session:
        product = await session.get(Product, product_id)
        print(f"    {product}")

    print("\n=== 3. SELECT with a WHERE clause — execute(select()) ===")
    print("""
  For anything more complex than a PK lookup, build a Select statement.
  result.scalar_one() asserts exactly one row is returned.
  result.scalars().all() returns a list.
""")
    async with db.get_session() as session:
        result = await session.execute(
            select(Product).where(Product.price < Decimal("80"))
        )
        cheap = result.scalars().all()
        print(f"    Products under $80:")
        for p in cheap:
            print(f"      {p}")

    print("\n=== 4. SELECT all — ordered ===")
    async with db.get_session() as session:
        result = await session.execute(
            select(Product).order_by(Product.price.desc())
        )
        for p in result.scalars().all():
            print(f"    {p}")


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

async def demo_update(product_id: int) -> None:
    print("\n=== 5. UPDATE — fetch, mutate, commit ===")
    print("""
  Same as sync: load the object, change its attributes, commit.
  session.refresh() reloads the object so you see DB-generated values
  (e.g. server defaults, triggers). Without it, the object's attributes
  are whatever you set — potentially stale if the DB modified them.
""")
    async with db.get_session() as session:
        product = await session.get(Product, product_id)
        old_price = product.price
        product.price = Decimal("89.99")
        await session.commit()
        await session.refresh(product)
        print(f"    {product.name}: {old_price} → {product.price}")


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

async def demo_delete(product_id: int) -> None:
    print("\n=== 6. DELETE ===")
    async with db.get_session() as session:
        product = await session.get(Product, product_id)
        await session.delete(product)
        await session.commit()
        print(f"    Deleted product {product_id}")

    async with db.get_session() as session:
        result = await session.execute(select(Product))
        remaining = result.scalars().all()
        print(f"    Remaining: {len(remaining)} products")
        for p in remaining:
            print(f"      {p}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    await db.reset_schema()

    products = await demo_insert()
    keyboard = products[0]
    hub = products[1]

    await demo_select(keyboard.id)
    await demo_update(keyboard.id)
    await demo_delete(hub.id)

    await db.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
