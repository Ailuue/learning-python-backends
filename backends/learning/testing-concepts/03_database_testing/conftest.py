"""
Test configuration for 03_database_testing/
============================================

Fixture dependency chain:

    engine (session-scoped)  — one SQLite engine for the whole test run
      └── db (function-scoped) — per-test session wrapped in a transaction
            ├── make_user        — factory fixture: creates User rows
            └── make_post        — factory fixture: creates Post rows

Isolation strategy: transaction rollback
    1. Open a connection, begin an outer transaction.
    2. Bind a Session to that connection with join_transaction_mode="create_savepoint".
       This makes session.commit() use SAVEPOINTs (nested transactions)
       rather than real commits, so the outer transaction stays open.
    3. After the test, roll back the outer transaction.
       Every INSERT / UPDATE / DELETE from the test vanishes instantly.
    Each test starts with a completely clean database. No truncation queries.
"""
import sys
import os

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

# Add the directory to sys.path so models.py and repository.py are importable.
sys.path.insert(0, os.path.dirname(__file__))

from models import Base, Post, User


# ---------------------------------------------------------------------------
# Engine — created once for the session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def engine():
    # SQLite in-memory: no file, no cleanup needed.
    # check_same_thread=False is required for SQLite when the connection is
    # shared across the setup/test/teardown boundary.
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # SQLite doesn't enforce foreign keys by default — this pragma enables them.
    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


# ---------------------------------------------------------------------------
# db — per-test session with transaction rollback
# ---------------------------------------------------------------------------

@pytest.fixture
def db(engine):
    """
    A Session that wraps each test in a transaction which is always rolled back.

    join_transaction_mode="create_savepoint" redirects session.commit() to
    issue SAVEPOINT / RELEASE SAVEPOINT instead of a real COMMIT. The outer
    transaction (connection.begin()) is never committed, so rollback at the
    end of the test undoes everything.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Factory fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def make_user(db: Session):
    """
    Returns a callable that creates a User with sensible defaults.
    Override individual fields as needed: make_user(username="alice").
    db.flush() assigns the auto-increment id without committing.
    """
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
        body: str = "Body content.",
        published: bool = False,
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
