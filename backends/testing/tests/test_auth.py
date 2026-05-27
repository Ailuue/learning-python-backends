"""
test_auth.py — authentication and ownership enforcement
=========================================================
Auth tests deserve their own file because they answer a distinct question:
"Does the app correctly gate access?" — not "does the business logic work?"

Two failure modes exist and both need coverage:
  - 401 Unauthorized: no identity provided, or the identity is invalid
  - 403 Forbidden: valid identity, but you don't own this resource

Parameterization is used throughout to verify that *every* protected route
rejects bad auth, not just the first one you thought to check.
"""

import pytest
from fastapi.testclient import TestClient


WRITE_ROUTES = [
    ("POST",   "/posts",      {"title": "x", "body": "y"}),
    ("PATCH",  "/posts/{id}", {"title": "x"}),
    ("DELETE", "/posts/{id}", None),
]


# ---------------------------------------------------------------------------
# 401 — missing or unknown X-User-Id
# ---------------------------------------------------------------------------

class TestMissingAuth:
    """
    When X-User-Id is completely absent, FastAPI returns 422 (not 401).

    Why 422?
    FastAPI validates all declared request parameters — including headers — before
    it calls the dependency function. Because `get_current_user` declares
    `x_user_id: int = Header(..., alias="X-User-Id")`, the `...` marks it as
    required. A missing header is a request validation error, so FastAPI short-
    circuits with 422 Unprocessable Entity before `get_current_user` runs.

    Contrast with `TestUnknownUser` below: when the header *is* present but
    refers to a non-existent user, the dependency *does* run, finds no User row,
    and explicitly raises HTTPException(401). That path returns 401.

    Real APIs typically make the header optional (`Header(None, ...)`) and check
    for None inside the dependency so that missing == 401 everywhere. For this
    module we keep the required-header approach to expose this FastAPI behaviour.
    """

    def test_create_post_requires_auth(self, client: TestClient):
        resp = client.post("/posts", json={"title": "x", "body": "y"})
        assert resp.status_code == 422  # required header missing → validation error

    def test_update_post_requires_auth(self, client: TestClient, make_user, make_post):
        user = make_user()
        post = make_post(user)
        resp = client.patch(f"/posts/{post.id}", json={"title": "x"})
        assert resp.status_code == 422

    def test_delete_post_requires_auth(self, client: TestClient, make_user, make_post):
        user = make_user()
        post = make_post(user)
        resp = client.delete(f"/posts/{post.id}")
        assert resp.status_code == 422


class TestUnknownUser:
    """X-User-Id header is present but refers to a user that doesn't exist."""

    def test_create_post_unknown_user(self, client: TestClient):
        resp = client.post(
            "/posts",
            json={"title": "x", "body": "y"},
            headers={"X-User-Id": "99999"},
        )
        assert resp.status_code == 401

    def test_update_post_unknown_user(self, client: TestClient, make_user, make_post):
        user = make_user()
        post = make_post(user)
        resp = client.patch(
            f"/posts/{post.id}",
            json={"title": "x"},
            headers={"X-User-Id": "99999"},
        )
        assert resp.status_code == 401

    def test_delete_post_unknown_user(self, client: TestClient, make_user, make_post):
        user = make_user()
        post = make_post(user)
        resp = client.delete(
            f"/posts/{post.id}",
            headers={"X-User-Id": "99999"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 403 — authenticated but not the owner
# ---------------------------------------------------------------------------

class TestOwnership:
    """
    Authenticated users may only modify their own posts.
    A valid user trying to edit or delete someone else's post gets 403.

    This is a separate concern from authentication (who are you?)
    and tests the authorization logic (are you allowed to do this?).
    """

    def test_update_another_users_post_returns_403(
        self, client: TestClient, make_user, make_post
    ):
        alice = make_user("alice")
        bob = make_user("bob")
        alices_post = make_post(alice)

        resp = client.patch(
            f"/posts/{alices_post.id}",
            json={"title": "Hijacked"},
            headers={"X-User-Id": str(bob.id)},
        )
        assert resp.status_code == 403

    def test_delete_another_users_post_returns_403(
        self, client: TestClient, make_user, make_post
    ):
        alice = make_user("alice")
        bob = make_user("bob")
        alices_post = make_post(alice)

        resp = client.delete(
            f"/posts/{alices_post.id}",
            headers={"X-User-Id": str(bob.id)},
        )
        assert resp.status_code == 403

    def test_owner_can_update_own_post(
        self, client: TestClient, make_user, make_post
    ):
        alice = make_user("alice")
        post = make_post(alice)

        resp = client.patch(
            f"/posts/{post.id}",
            json={"title": "My edit"},
            headers={"X-User-Id": str(alice.id)},
        )
        assert resp.status_code == 200

    def test_owner_can_delete_own_post(
        self, client: TestClient, make_user, make_post
    ):
        alice = make_user("alice")
        post = make_post(alice)

        resp = client.delete(
            f"/posts/{post.id}",
            headers={"X-User-Id": str(alice.id)},
        )
        assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Read routes are public
# ---------------------------------------------------------------------------

class TestPublicRoutes:
    """GET routes require no auth. These confirm the boundary is correct."""

    def test_list_posts_is_public(self, client: TestClient):
        resp = client.get("/posts")
        assert resp.status_code == 200

    def test_get_post_is_public(self, client: TestClient, make_user, make_post):
        user = make_user()
        post = make_post(user)
        resp = client.get(f"/posts/{post.id}")
        assert resp.status_code == 200
