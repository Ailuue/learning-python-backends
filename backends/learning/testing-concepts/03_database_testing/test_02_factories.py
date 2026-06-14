"""
Factory Fixtures
================
Factory fixtures return a *callable* rather than a fixed object. The test
calls the callable to create instances, passing only the fields that matter
for the scenario being tested. Everything else gets a sensible default.

Benefits over plain fixtures that return a single object:
  - Create multiple objects in one test (make_user("alice"), make_user("bob"))
  - Override only the fields relevant to the test case
  - Readable: the test shows intent ("give me a published post"), not boilerplate

Pattern:
    @pytest.fixture
    def make_user(db):
        def _factory(username="alice", ...):
            ...
        return _factory     ← returns the callable, not a User

Internally, db.flush() assigns the auto-increment id without committing, so
the object is queryable within the test's transaction but gone after rollback.

Run:
    pytest 03_database_testing/test_02_factories.py -v
"""

from sqlalchemy.orm import Session

import repository


# ---------------------------------------------------------------------------
# Basic factory usage
# ---------------------------------------------------------------------------

class TestUserFactory:
    def test_default_username(self, db: Session, make_user):
        user = make_user()
        assert user.username == "alice"
        assert user.email == "alice@example.com"

    def test_custom_username(self, db: Session, make_user):
        user = make_user(username="bob")
        assert user.username == "bob"
        assert user.email == "bob@example.com"

    def test_custom_email_override(self, db: Session, make_user):
        user = make_user(username="carol", email="work@corp.com")
        assert user.email == "work@corp.com"

    def test_factory_assigns_id(self, db: Session, make_user):
        user = make_user()
        assert user.id is not None

    def test_multiple_users_have_different_ids(self, db: Session, make_user):
        alice = make_user("alice")
        bob   = make_user("bob")
        assert alice.id != bob.id


# ---------------------------------------------------------------------------
# Building multi-object scenarios
# ---------------------------------------------------------------------------

class TestPostFactory:
    def test_post_linked_to_user(self, db: Session, make_user, make_post):
        user = make_user()
        post = make_post(user)

        assert post.user_id == user.id

    def test_default_post_is_unpublished(self, db: Session, make_user, make_post):
        user = make_user()
        post = make_post(user)
        assert post.published is False

    def test_published_flag_override(self, db: Session, make_user, make_post):
        user = make_user()
        post = make_post(user, published=True)
        assert post.published is True

    def test_post_title_override(self, db: Session, make_user, make_post):
        user = make_user()
        post = make_post(user, title="My Custom Title")
        assert post.title == "My Custom Title"


# ---------------------------------------------------------------------------
# Testing repository queries with factory-built data
# ---------------------------------------------------------------------------

class TestPublishedPostsQuery:
    def test_only_published_posts_returned(self, db: Session, make_user, make_post):
        author = make_user()
        make_post(author, title="Draft Post",     published=False)
        make_post(author, title="Published Post", published=True)

        posts = repository.get_published_posts(db)

        titles = [p.title for p in posts]
        assert "Published Post" in titles
        assert "Draft Post" not in titles

    def test_multiple_published_posts(self, db: Session, make_user, make_post):
        author = make_user()
        make_post(author, title="Post A", published=True)
        make_post(author, title="Post B", published=True)
        make_post(author, title="Post C", published=False)

        posts = repository.get_published_posts(db)
        assert len(posts) == 2


class TestGetPostsByUser:
    def test_returns_only_this_users_posts(self, db: Session, make_user, make_post):
        alice = make_user("alice")
        bob   = make_user("bob")
        make_post(alice, title="Alice's post")
        make_post(bob,   title="Bob's post")

        alices_posts = repository.get_posts_by_user(db, alice)

        assert len(alices_posts) == 1
        assert alices_posts[0].title == "Alice's post"

    def test_returns_empty_list_for_user_with_no_posts(
        self, db: Session, make_user
    ):
        user = make_user()
        posts = repository.get_posts_by_user(db, user)
        assert posts == []


# ---------------------------------------------------------------------------
# Cascade delete — deleting a user removes their posts
# ---------------------------------------------------------------------------

class TestCascadeDelete:
    def test_deleting_user_removes_their_posts(self, db: Session, make_user, make_post):
        user = make_user()
        post = make_post(user, title="Will be deleted")
        post_id = post.id

        repository.delete_user(db, user)
        db.expire_all()

        remaining = repository.get_published_posts(db)
        assert all(p.id != post_id for p in remaining)
