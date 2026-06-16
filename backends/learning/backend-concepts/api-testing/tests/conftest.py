"""
Test configuration and shared fixtures
=======================================
The three core decisions in any database-backed API test suite:

  1. Which database to use
     Options: production db (dangerous), separate test db, SQLite in-memory.
     This module uses a real PostgreSQL test database. SQLite is faster to
     spin up but silently differs from PostgreSQL: it ignores CHECK constraints
     by default, has no SERIAL sequences, and misses operators like @@. Tests
     that pass on SQLite can fail in production against PostgreSQL.

  2. How to isolate tests from each other
     Options: truncate tables between tests, drop/recreate schema, or wrap
     each test in a transaction and roll it back.
     This module uses transaction rollback — the fastest approach. Each test
     runs inside an open transaction. After the test, the transaction is rolled
     back rather than committed, so the database returns to its pre-test state
     automatically. No truncation queries needed.

  3. How to share the test session with the app
     FastAPI uses dependency injection for the database session. We override
     get_db to yield the same connection-bound session the test uses. This
     ensures the app and the test see the same uncommitted data within the
     rolled-back transaction.

The fixture dependency chain:

  engine (session-scoped)
    └── db (function-scoped) ← wraps each test in a transaction
          └── client (function-scoped) ← TestClient with db override
                └── make_user, make_post ← factory fixtures that use db
"""

import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

load_dotenv()

from app.database import get_db
from app.main import app
from app.models import Base, Post, User

# ---------------------------------------------------------------------------
# Engine — one engine for the entire test session
# ---------------------------------------------------------------------------

_engine = create_engine(os.environ["DATABASE_URL"])


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once before any test runs; drop them all at the end."""
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


# ---------------------------------------------------------------------------
# db — transaction rollback isolation
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    """
    Per-test database session backed by a transaction that is always rolled back.

    How it works:
      1. Open a connection and begin an outer transaction.
      2. Create a Session bound to that connection with
         join_transaction_mode="create_savepoint".
         This makes session.commit() use SAVEPOINTs (nested transactions)
         instead of real commits. The app calls commit() as normal, but those
         commits only release savepoints — the outer transaction stays open.
      3. After the test finishes (pass or fail), rollback the outer transaction.
         Every INSERT, UPDATE, and DELETE from the test disappears.

    Result: each test starts with a clean database. No truncation needed,
    no inter-test pollution, and it's fast because no DDL is involved.
    """
    connection = _engine.connect()
    transaction = connection.begin()
    session = Session(connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# client — TestClient wired to the test db session
# ---------------------------------------------------------------------------

@pytest.fixture
def client(db: Session):
    """
    FastAPI TestClient whose database dependency is overridden to use the
    same connection-bound session as the test.

    Without this override, the app would open a new session on each request
    using a different connection. That session would not see the uncommitted
    test data created by factory fixtures, so e.g. a user created by make_user
    would be invisible to the POST /posts auth dependency.

    app.dependency_overrides replaces get_db for the duration of this fixture,
    then clears the override so other test modules are not affected.
    """
    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Factory fixtures
# ---------------------------------------------------------------------------
#
# Factories are fixtures that return a callable. Tests call the callable
# to create as many objects as they need, with customisable attributes.
# db.flush() assigns auto-increment IDs without committing, so the objects
# are visible within the transaction but not persisted beyond the test.

@pytest.fixture
def make_user(db: Session):
    def _factory(username: str = "alice", email: str | None = None) -> User:
        user = User(
            username=username,
            email=email or f"{username}@example.com",
        )
        db.add(user)
        db.flush()
        return user
    return _factory


@pytest.fixture
def make_post(db: Session):
    def _factory(
        user: User,
        title: str = "Test Post",
        body: str = "Body text.",
        published: bool = True,
    ) -> Post:
        post = Post(
            user_id=user.id,
            title=title,
            body=body,
            published=published,
        )
        db.add(post)
        db.flush()
        return post
    return _factory
