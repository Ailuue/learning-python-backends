"""
test_posts.py — CRUD endpoint tests
=====================================
These tests cover the happy paths for every route, plus a few error cases
that belong to the route logic itself (not auth, not validation — those get
their own files so failures are easy to locate).

Two verification styles appear in this file, and both matter:

  1. Response assertions — check status code and JSON body.
     Fast, but only proves the HTTP layer worked.

  2. DB state assertions — after a write, query the database directly
     (using the `db` fixture) to confirm the change was actually persisted
     inside the transaction.
     This catches bugs where the route returns 201 but forgot to commit, or
     returns the wrong object, or silently mutates the wrong row.

Combining both styles is idiomatic for database-backed API tests.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Post


# ---------------------------------------------------------------------------
# GET /posts
# ---------------------------------------------------------------------------

class TestListPosts:
    def test_empty_list(self, client: TestClient):
        resp = client.get("/posts")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_published_posts(self, client: TestClient, make_user, make_post):
        user = make_user()
        make_post(user, title="Published", published=True)
        make_post(user, title="Draft", published=False)

        resp = client.get("/posts")
        assert resp.status_code == 200
        titles = [p["title"] for p in resp.json()]
        assert "Published" in titles
        assert "Draft" not in titles

    def test_filter_by_author(self, client: TestClient, make_user, make_post):
        alice = make_user("alice")
        bob = make_user("bob")
        make_post(alice, title="Alice's post")
        make_post(bob, title="Bob's post")

        resp = client.get(f"/posts?author_id={alice.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Alice's post"

    def test_returns_newest_first(self, client: TestClient, make_user, make_post):
        user = make_user()
        make_post(user, title="First")
        make_post(user, title="Second")
        make_post(user, title="Third")

        resp = client.get("/posts")
        titles = [p["title"] for p in resp.json()]
        assert titles == ["Third", "Second", "First"]


# ---------------------------------------------------------------------------
# GET /posts/{post_id}
# ---------------------------------------------------------------------------

class TestGetPost:
    def test_returns_post(self, client: TestClient, make_user, make_post):
        user = make_user()
        post = make_post(user, title="Hello")

        resp = client.get(f"/posts/{post.id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Hello"
        assert resp.json()["id"] == post.id

    def test_404_for_missing_post(self, client: TestClient):
        resp = client.get("/posts/99999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /posts
# ---------------------------------------------------------------------------

class TestCreatePost:
    def test_creates_post(self, client: TestClient, db: Session, make_user):
        user = make_user()

        resp = client.post(
            "/posts",
            json={"title": "New Post", "body": "Some content."},
            headers={"X-User-Id": str(user.id)},
        )

        # 1. Response assertions
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "New Post"
        assert data["body"] == "Some content."
        assert data["user_id"] == user.id
        assert data["published"] is False  # default

        # 2. DB state assertions — the row must exist in the database
        post_id = data["id"]
        post = db.get(Post, post_id)
        assert post is not None
        assert post.title == "New Post"
        assert post.user_id == user.id

    def test_post_belongs_to_authenticated_user(
        self, client: TestClient, db: Session, make_user
    ):
        alice = make_user("alice")
        bob = make_user("bob")

        resp = client.post(
            "/posts",
            json={"title": "Alice's post", "body": "..."},
            headers={"X-User-Id": str(alice.id)},
        )
        assert resp.status_code == 201
        post = db.get(Post, resp.json()["id"])
        assert post.user_id == alice.id
        assert post.user_id != bob.id


# ---------------------------------------------------------------------------
# PATCH /posts/{post_id}
# ---------------------------------------------------------------------------

class TestUpdatePost:
    def test_updates_title(self, client: TestClient, db: Session, make_user, make_post):
        user = make_user()
        post = make_post(user, title="Old title")

        resp = client.patch(
            f"/posts/{post.id}",
            json={"title": "New title"},
            headers={"X-User-Id": str(user.id)},
        )

        # 1. Response assertions
        assert resp.status_code == 200
        assert resp.json()["title"] == "New title"

        # 2. DB state assertions
        db.refresh(post)
        assert post.title == "New title"

    def test_updates_published_flag(
        self, client: TestClient, db: Session, make_user, make_post
    ):
        user = make_user()
        post = make_post(user, published=False)

        client.patch(
            f"/posts/{post.id}",
            json={"published": True},
            headers={"X-User-Id": str(user.id)},
        )

        db.refresh(post)
        assert post.published is True

    def test_partial_update_leaves_other_fields_intact(
        self, client: TestClient, db: Session, make_user, make_post
    ):
        user = make_user()
        post = make_post(user, title="Keep me", body="Keep this too.")

        client.patch(
            f"/posts/{post.id}",
            json={"published": True},
            headers={"X-User-Id": str(user.id)},
        )

        db.refresh(post)
        assert post.title == "Keep me"
        assert post.body == "Keep this too."

    def test_404_for_missing_post(self, client: TestClient, make_user):
        user = make_user()
        resp = client.patch(
            "/posts/99999",
            json={"title": "x"},
            headers={"X-User-Id": str(user.id)},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /posts/{post_id}
# ---------------------------------------------------------------------------

class TestDeletePost:
    def test_deletes_post(self, client: TestClient, db: Session, make_user, make_post):
        user = make_user()
        post = make_post(user)
        post_id = post.id

        resp = client.delete(
            f"/posts/{post_id}",
            headers={"X-User-Id": str(user.id)},
        )

        # 1. Response assertion
        assert resp.status_code == 204

        # 2. DB state assertion — row must be gone
        db.expire_all()  # clear identity map cache before re-querying
        assert db.get(Post, post_id) is None

    def test_deleted_post_no_longer_listed(
        self, client: TestClient, make_user, make_post
    ):
        user = make_user()
        post = make_post(user, title="Gone soon")

        client.delete(f"/posts/{post.id}", headers={"X-User-Id": str(user.id)})

        resp = client.get("/posts")
        titles = [p["title"] for p in resp.json()]
        assert "Gone soon" not in titles

    def test_404_for_missing_post(self, client: TestClient, make_user):
        user = make_user()
        resp = client.delete(
            "/posts/99999",
            headers={"X-User-Id": str(user.id)},
        )
        assert resp.status_code == 404
