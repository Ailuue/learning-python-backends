"""
Test Isolation
==============
Each test receives a fresh database because the `db` fixture wraps it in a
transaction that is rolled back at the end — not committed.

The tests below prove this directly: data created in one test is invisible
in the next, and the state assertions hold regardless of execution order.

Why this matters:
  - Tests that share state can produce "ghost failures" where test B passes
    or fails depending on whether test A ran first.
  - Rollback is much faster than TRUNCATE (no DDL, no auto-increment reset).
  - No teardown logic to write — the fixture handles it automatically.

Run:
    pytest 03_database_testing/test_01_isolation.py -v
"""

import pytest
from sqlalchemy.orm import Session

import repository
from models import User


# ---------------------------------------------------------------------------
# Basic CRUD
# ---------------------------------------------------------------------------

class TestCreateUser:
    def test_creates_user_with_correct_fields(self, db: Session):
        user = repository.create_user(db, username="alice", email="alice@example.com")

        assert user.id is not None
        assert user.username == "alice"
        assert user.email == "alice@example.com"

    def test_two_users_get_different_ids(self, db: Session):
        alice = repository.create_user(db, username="alice", email="alice@example.com")
        bob   = repository.create_user(db, username="bob",   email="bob@example.com")

        assert alice.id != bob.id


class TestGetUser:
    def test_get_by_id_returns_user(self, db: Session):
        created = repository.create_user(db, username="alice", email="alice@example.com")

        fetched = repository.get_user_by_id(db, created.id)

        assert fetched is not None
        assert fetched.username == "alice"

    def test_get_by_id_returns_none_for_unknown_id(self, db: Session):
        assert repository.get_user_by_id(db, 99999) is None

    def test_get_by_email_returns_user(self, db: Session):
        repository.create_user(db, username="bob", email="bob@example.com")

        user = repository.get_user_by_email(db, "bob@example.com")

        assert user is not None
        assert user.username == "bob"

    def test_get_by_email_returns_none_for_unknown(self, db: Session):
        assert repository.get_user_by_email(db, "ghost@example.com") is None


class TestDeleteUser:
    def test_deleted_user_is_not_found(self, db: Session):
        user = repository.create_user(db, username="carol", email="carol@example.com")
        user_id = user.id

        repository.delete_user(db, user)

        assert repository.get_user_by_id(db, user_id) is None


# ---------------------------------------------------------------------------
# Isolation proof — these tests run in sequence; data must not bleed over.
# ---------------------------------------------------------------------------

class TestIsolation:
    def test_first_test_creates_a_user(self, db: Session):
        repository.create_user(db, username="isolation_user", email="iso@example.com")
        users = repository.list_users(db)
        assert len(users) == 1

    def test_second_test_sees_empty_database(self, db: Session):
        # If rollback worked, there are zero rows — isolation_user is gone.
        users = repository.list_users(db)
        assert len(users) == 0, (
            f"Expected 0 users but found {len(users)}. "
            "This means test data leaked from the previous test — rollback failed."
        )

    def test_write_and_verify_state_in_same_test(self, db: Session):
        repository.create_user(db, username="alice", email="alice@example.com")
        repository.create_user(db, username="bob",   email="bob@example.com")

        users = repository.list_users(db)
        usernames = [u.username for u in users]

        assert "alice" in usernames
        assert "bob" in usernames
        assert len(users) == 2
