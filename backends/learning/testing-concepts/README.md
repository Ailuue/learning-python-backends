# Testing

> 📚 [Backend Learning](../README.md) · **Core path · step 2 of 4** · [⬅ fast-api-tutorial](../fast-api-tutorial/) · Next: [database-concepts ➡](../database-concepts/)

## What is this?

Writing tests is as important as writing the code itself. A good test suite lets you refactor with confidence, catch regressions before they ship, and document intended behaviour in executable form.

**pytest** is Python's dominant testing framework. It's far more ergonomic than `unittest` and has a rich plugin ecosystem.

This module covers the testing concepts a backend engineer reaches for daily:

- **pytest basics** — how pytest discovers tests, fixtures for setup/teardown, parametrize for data-driven tests, and marks for filtering
- **Mocking** — replacing real dependencies (databases, email services, external APIs) with controlled fakes using `unittest.mock`
- **Database testing** — isolating tests with transaction rollback so every test starts from a clean slate
- **Async testing** — testing `async` functions and async SQLAlchemy with `pytest-asyncio`

> **See also:** `backend-concepts/testing/` for a complete production-style integration test suite (FastAPI + PostgreSQL, factory fixtures, dependency overrides).

## What the sections cover

| Section | What it teaches |
|---|---|
| `01_pytest_basics/` | pytest anatomy, fixtures (scope, yield, composition), parametrize, marks |
| `02_mocking/` | `patch`, `MagicMock`, `side_effect`, `autospec` — controlling external boundaries |
| `03_database_testing/` | Transaction rollback isolation, factory fixtures, SQLite for fast standalone tests |
| `04_async_testing/` | `pytest-asyncio`, async fixtures, testing async SQLAlchemy repositories |

## How to run

```bash
pip install -r requirements.txt

# Run everything
pytest

# Run a specific section
pytest 01_pytest_basics/ -v
pytest 02_mocking/ -v
pytest 03_database_testing/ -v
pytest 04_async_testing/ -v

# Run only fast unit tests (no db)
pytest -m "not db and not asyncdb" -v
```
