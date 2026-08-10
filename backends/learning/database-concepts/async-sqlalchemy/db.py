"""
Shared async database layer for all scripts in this directory.

The DATABASE_URL must use the postgresql+asyncpg:// scheme — asyncpg is a
pure-Python async PostgreSQL driver that never blocks the event loop.

Key difference from the sync layer you've used before:
  - create_async_engine  instead of  create_engine
  - async_sessionmaker   instead of  sessionmaker
  - AsyncSession         instead of  Session
  - every session method needs await
  - run_sync() to execute synchronous DDL (drop_all / create_all)
"""

import os
from contextlib import asynccontextmanager
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy import Numeric, String
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

load_dotenv()


def make_engine(
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_timeout: float = 30.0,
    pool_pre_ping: bool = True,
    pool_recycle: int = -1,
    echo: bool = False,
) -> AsyncEngine:
    """
    Create an async engine with configurable pool settings.

    pool_size     — persistent connections kept open and reused
    max_overflow  — extra connections allowed above pool_size (temporary)
    pool_timeout  — seconds to wait for a free connection before raising
    pool_pre_ping — send SELECT 1 before using a connection to detect stale ones
    pool_recycle  — discard connections older than this many seconds (-1 = never)
    """
    return create_async_engine(
        os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/async_pool_demo",
        ),
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_pre_ping=pool_pre_ping,
        pool_recycle=pool_recycle,
        echo=echo,
    )


# Default engine used by scripts that don't need custom pool settings.
engine = make_engine()

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id:    Mapped[int]     = mapped_column(primary_key=True)
    name:  Mapped[str]     = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock: Mapped[int]     = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"Product(id={self.id}, name={self.name!r}, price={self.price}, stock={self.stock})"


@asynccontextmanager
async def get_session():
    async with AsyncSessionFactory() as session:
        yield session


async def reset_schema(eng: AsyncEngine | None = None) -> None:
    eng = eng or engine
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def seed(session: AsyncSession) -> list[Product]:
    products = [
        Product(name="Wireless Keyboard", price=Decimal("79.99"), stock=42),
        Product(name="USB-C Hub",         price=Decimal("49.99"), stock=130),
        Product(name="Monitor Stand",     price=Decimal("34.99"), stock=17),
    ]
    session.add_all(products)
    await session.commit()
    for p in products:
        await session.refresh(p)
    return products


def print_pool_status(eng: AsyncEngine, label: str = "Pool status") -> None:
    pool = eng.sync_engine.pool
    print(f"\n  [{label}]")
    print(f"    pool_size (max persistent): {pool.size()}")
    print(f"    checked in  (idle):         {pool.checkedin()}")
    print(f"    checked out (in use):       {pool.checkedout()}")
    print(f"    overflow in use:            {max(0, pool.overflow())}")
