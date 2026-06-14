"""
Async Database Testing
======================
The async repository in async_repository.py uses async SQLAlchemy sessions.
Testing it requires async fixtures and async test functions.

The isolation strategy is identical to the sync version in 03_database_testing/:
wrap each test in a transaction that is rolled back after the test completes.
The `db` fixture in conftest.py handles this.

Compare this file with 03_database_testing/test_02_factories.py to see how
sync and async testing patterns mirror each other.

Run:
    pytest 04_async_testing/test_02_async_db.py -v
"""

from sqlalchemy.ext.asyncio import AsyncSession

import async_repository as repository


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

class TestAsyncCreateUser:
    async def test_creates_user_with_correct_fields(self, db: AsyncSession):
        user = await repository.create_user(db, "alice", "alice@example.com")

        assert user.id is not None
        assert user.username == "alice"
        assert user.email == "alice@example.com"

    async def test_two_users_get_different_ids(self, db: AsyncSession):
        alice = await repository.create_user(db, "alice", "alice@example.com")
        bob   = await repository.create_user(db, "bob",   "bob@example.com")

        assert alice.id != bob.id


class TestAsyncGetUser:
    async def test_get_by_id_returns_user(self, db: AsyncSession):
        created = await repository.create_user(db, "alice", "alice@example.com")

        fetched = await repository.get_user_by_id(db, created.id)

        assert fetched is not None
        assert fetched.username == "alice"

    async def test_get_by_id_returns_none_for_missing(self, db: AsyncSession):
        assert await repository.get_user_by_id(db, 99999) is None

    async def test_get_by_email(self, db: AsyncSession):
        await repository.create_user(db, "bob", "bob@example.com")

        user = await repository.get_user_by_email(db, "bob@example.com")

        assert user is not None
        assert user.username == "bob"


# ---------------------------------------------------------------------------
# Isolation — same proof as the sync version
# ---------------------------------------------------------------------------

class TestAsyncIsolation:
    async def test_first_test_creates_data(self, db: AsyncSession):
        await repository.create_user(db, "isolation_user", "iso@example.com")
        users = await repository.list_users(db)
        assert len(users) == 1

    async def test_second_test_starts_clean(self, db: AsyncSession):
        users = await repository.list_users(db)
        assert len(users) == 0, (
            f"Expected 0 users, found {len(users)}. Rollback didn't work."
        )


# ---------------------------------------------------------------------------
# Query tests using factory fixtures
# ---------------------------------------------------------------------------

class TestAsyncPostQueries:
    async def test_only_published_posts_returned(
        self, db: AsyncSession, make_user, make_post
    ):
        author = await make_user()
        await make_post(author, title="Draft",     published=False)
        await make_post(author, title="Published", published=True)

        posts = await repository.get_published_posts(db)

        titles = [p.title for p in posts]
        assert "Published" in titles
        assert "Draft" not in titles

    async def test_get_posts_by_user_filters_correctly(
        self, db: AsyncSession, make_user, make_post
    ):
        alice = await make_user("alice")
        bob   = await make_user("bob")
        await make_post(alice, title="Alice's post")
        await make_post(bob,   title="Bob's post")

        alice_posts = await repository.get_posts_by_user(db, alice)

        assert len(alice_posts) == 1
        assert alice_posts[0].title == "Alice's post"

    async def test_user_with_no_posts_returns_empty(
        self, db: AsyncSession, make_user
    ):
        user = await make_user()
        posts = await repository.get_posts_by_user(db, user)
        assert posts == []

    async def test_multiple_posts_for_same_user(
        self, db: AsyncSession, make_user, make_post
    ):
        author = await make_user()
        await make_post(author, title="Post 1", published=True)
        await make_post(author, title="Post 2", published=True)
        await make_post(author, title="Post 3", published=False)

        published = await repository.get_published_posts(db)
        assert len(published) == 2

        all_posts = await repository.get_posts_by_user(db, author)
        assert len(all_posts) == 3
