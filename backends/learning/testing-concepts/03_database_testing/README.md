# Database Testing

## What is this?

The central challenge of testing database code is **isolation**: each test must start from a clean slate so tests can run in any order without interfering with each other.

The naive approach — `DELETE FROM ...` or dropping and recreating the schema between tests — is slow. The standard approach is **transaction rollback**:

1. Open a connection and begin an outer transaction.
2. Bind the session to that connection.
3. Run the test — any `commit()` inside the code uses a savepoint, not a real commit, so data is never actually persisted.
4. After the test, roll back the outer transaction. Every write disappears instantly with no DDL.

This module uses **SQLite** so it runs standalone with no Docker required. The same patterns apply identically to PostgreSQL (which is what `backend-concepts/testing/` uses).

## What the files cover

| File | What it teaches |
|---|---|
| `models.py` | SQLAlchemy 2.0 models (User, Post) |
| `repository.py` | Data access layer — the code under test |
| `conftest.py` | Engine + transaction-rollback session fixture + factory fixtures |
| `test_01_isolation.py` | Proving that test data doesn't bleed between tests |
| `test_02_factories.py` | Factory fixtures: building realistic test data with sensible defaults |

## How to run

```bash
# No database setup needed — SQLite runs in memory
pytest 03_database_testing/ -v
```
