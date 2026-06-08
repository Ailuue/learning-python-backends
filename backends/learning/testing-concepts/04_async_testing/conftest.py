"""
Async test configuration for 04_async_testing/
================================================

asyncio_mode = "auto" (set in pytest.ini) means every async def test_ and
async def fixture runs automatically inside an event loop — no
@pytest.mark.asyncio decorator needed.

Fixture dependency chain:

    async_engine (session-scoped) — one aiosqlite engine for the run
      └── db (function-scoped) — per-test async session with rollback
            ├── make_user        — async factory
            └── make_post        — async factory

The rollback isolation strategy is the same as in 03_database_testing/:
async_engine.begin() opens an outer transaction; we bind the async session
to that connection; after the test we roll back. SQLite doesn't support
true nested transactions (SAVEPOINTs with aiosqlite in the same way), so we
use a slightly different approach: we use begin_nested() for the inner
savepoint that session.commit() issues.
"""
import sys
import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

sys.path.insert(0, os.path.dirname(__file__))

from async_models import Base, Post, User


# ---------------------------------------------------------------------------
# Engine — one per test session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ---------------------------------------------------------------------------
# db — per-test async session with transaction rollback
# ---------------------------------------------------------------------------

@pytest.fixture
async def db(async_engine):
    """
    Async session scoped to a single test.

    We use begin_nested() to create a SAVEPOINT before yielding the session,
    then roll back to that savepoint after the test. This means any
    session.commit() inside the test only releases the inner savepoint —
    the outer transaction remains and is rolled back at the end.
    """
    async with async_engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested()   # savepoint — all test writes land here

        session = AsyncSession(conn, join_transaction_mode="create_savepoint")

        yield session

        await session.close()
        await conn.rollback()       # rolls back to before the savepoint


# ---------------------------------------------------------------------------
# Factory fixtures (async)
# ---------------------------------------------------------------------------

@pytest.fixture
async def make_user(db: AsyncSession):
    async def _factory(username: str = "alice", email: str | None = None) -> User:
        from async_repository import create_user
        return await create_user(db, username, email or f"{username}@example.com")
    return _factory


@pytest.fixture
async def make_post(db: AsyncSession):
    async def _factory(
        user: User,
        title: str = "Test Post",
        body: str = "Body content.",
        published: bool = False,
    ) -> Post:
        from async_repository import create_post
        return await create_post(db, user, title, body, published)
    return _factory
