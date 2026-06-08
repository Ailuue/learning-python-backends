# Async Testing

## What is this?

Modern Python backends often use `async`/`await` for I/O — especially with async database drivers, HTTP clients, and message brokers. Testing async code requires a running event loop and async-aware fixtures.

**pytest-asyncio** handles this. It provides an async test runner and lets you write `async def test_...` functions and `async def` fixtures naturally.

```python
# Without pytest-asyncio — this would silently pass without running the body
async def test_something():
    result = await some_async_function()
    assert result == expected

# With pytest-asyncio (asyncio_mode = "auto" in pytest.ini)
# The decorator is applied automatically and the body actually runs.
```

This module uses **aiosqlite** (async SQLite driver) to keep things self-contained — no Docker needed. The patterns are identical with `asyncpg` or any other async database driver.

## What the files cover

| File | What it teaches |
|---|---|
| `async_models.py` | SQLAlchemy 2.0 models for the async engine |
| `async_repository.py` | Async repository using `async with session` |
| `conftest.py` | Async engine fixture, async session with rollback, async factory fixtures |
| `test_01_async_functions.py` | Testing pure async functions, async context managers, `asyncio.gather` |
| `test_02_async_db.py` | Testing async repository queries, async session isolation |

## How to run

```bash
# asyncio_mode = auto is set in pytest.ini — no @pytest.mark.asyncio needed
pytest 04_async_testing/ -v
```
