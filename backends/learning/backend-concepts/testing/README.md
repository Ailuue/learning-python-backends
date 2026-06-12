# Testing (Backend Concepts)

A minimal FastAPI app used to practice core testing patterns with pytest.

For a deeper treatment of testing topics, see [testing-concepts/](../../testing-concepts/).

## What's here

A small Posts API (`app/`) with:
- SQLite database via SQLAlchemy
- Simplified header-based auth (`X-User-Id`) — the same dependency-injection pattern used with JWT, just without the cryptography
- Three test files:
  - `test_auth.py` — missing/invalid auth header
  - `test_posts.py` — create, read, update, delete
  - `test_validation.py` — request body validation errors

## Key patterns demonstrated

**Overriding a FastAPI dependency in tests:**
```python
def override_db():
    # use a separate in-memory database per test
    yield test_session

app.dependency_overrides[get_db] = override_db
```

**Using `TestClient` for synchronous route tests:**
```python
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.post("/posts", json={"title": "Hi"}, headers={"X-User-Id": "1"})
assert response.status_code == 201
```

## Setup

```bash
pip install -r requirements.txt
pytest
```
