"""
Integration tests — run these inside the Docker environment where
DB and Redis are reachable.

HOW TO RUN:

  # Option 1: exec into the already-running dev container
  # (uses the bind mount, so tests see your latest unsaved edits too)
  docker compose exec app python -m pytest tests/ -v

  # Option 2: fresh container via the test compose override
  # (no bind mount — tests the built image exactly as deployed)
  docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm app

  # Option 3: run during active dev without rebuilding
  docker compose run --rm app python -m pytest tests/ -v --tb=short

The key difference: exec runs inside an existing container; run spins up a new one.
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestRoot:
    def test_returns_200(self):
        r = client.get("/")
        assert r.status_code == 200

    def test_response_shape(self):
        r = client.get("/")
        data = r.json()
        assert "message" in data
        assert "env" in data

    def test_request_id_header_present(self):
        # The middleware we added attaches X-Request-ID to every response.
        r = client.get("/")
        assert "x-request-id" in r.headers
        assert len(r.headers["x-request-id"]) == 8   # uuid4().hex[:8]

    def test_each_request_gets_unique_id(self):
        ids = {client.get("/").headers["x-request-id"] for _ in range(5)}
        assert len(ids) == 5   # all different


class TestHealth:
    def test_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_response_shape(self):
        r = client.get("/health")
        data = r.json()
        assert "status" in data
        assert "db" in data
        assert "redis" in data

    def test_db_and_redis_reachable(self):
        # When run inside docker compose, both should be True.
        # If this fails, check: docker compose ps (are db and redis healthy?)
        r = client.get("/health")
        data = r.json()
        assert data["db"] is True, "db is not reachable — is the db service healthy?"
        assert data["redis"] is True, "redis is not reachable — is the redis service healthy?"
        assert data["status"] == "ok"


class TestItems:
    def test_list_returns_correct_shape(self):
        r = client.get("/items")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "source" in data
        assert data["source"] in ("db", "cache")

    def test_second_request_served_from_cache(self):
        client.delete("/items/cache")   # ensure clean state
        r1 = client.get("/items")
        r2 = client.get("/items")
        assert r1.json()["source"] == "db"
        assert r2.json()["source"] == "cache"

    def test_create_item_returns_201(self):
        r = client.post("/items", json={"name": "pytest-item", "description": "created by test"})
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "pytest-item"
        assert "id" in data

    def test_create_item_invalidates_cache(self):
        client.get("/items")                           # prime cache
        client.post("/items", json={"name": "cache-buster"})
        r = client.get("/items")                       # cache should be gone
        assert r.json()["source"] == "db"

    def test_created_item_appears_in_list(self):
        client.delete("/items/cache")
        r_create = client.post("/items", json={"name": "appears-in-list"})
        new_id = r_create.json()["id"]

        r_list = client.get("/items")
        ids = [item["id"] for item in r_list.json()["items"]]
        assert new_id in ids

    def test_bust_cache_returns_200(self):
        r = client.delete("/items/cache")
        assert r.status_code == 200
