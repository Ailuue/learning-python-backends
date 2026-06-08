"""
Testing Async Functions
=======================
pytest-asyncio makes async tests work by running each async test function
inside an event loop. With asyncio_mode = "auto" (set in pytest.ini),
this happens automatically — no @pytest.mark.asyncio needed.

Key points:
  - async def test_... works exactly like def test_... for assertions
  - await inside tests works naturally
  - asyncio.gather lets you run multiple coroutines concurrently in tests
  - Mocking async functions requires AsyncMock (not MagicMock)

Run:
    pytest 04_async_testing/test_01_async_functions.py -v
"""

import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Async functions under test
# ---------------------------------------------------------------------------

async def fetch_user(user_id: int) -> dict:
    await asyncio.sleep(0)   # simulates I/O without actually waiting
    if user_id <= 0:
        raise ValueError(f"Invalid user_id: {user_id}")
    return {"id": user_id, "username": f"user_{user_id}"}


async def fetch_users_concurrently(user_ids: list[int]) -> list[dict]:
    return await asyncio.gather(*[fetch_user(uid) for uid in user_ids])


async def call_external_api(client, endpoint: str) -> dict:
    response = await client.get(endpoint)
    return response


# ---------------------------------------------------------------------------
# 1. Basic async test — await works normally
# ---------------------------------------------------------------------------

async def test_fetch_user_returns_dict():
    user = await fetch_user(1)
    assert user["id"] == 1
    assert user["username"] == "user_1"


async def test_fetch_user_raises_for_invalid_id():
    with pytest.raises(ValueError, match="Invalid user_id"):
        await fetch_user(-1)


# ---------------------------------------------------------------------------
# 2. asyncio.gather — testing concurrent execution
# ---------------------------------------------------------------------------

async def test_fetch_users_concurrently():
    users = await fetch_users_concurrently([1, 2, 3])

    assert len(users) == 3
    ids = {u["id"] for u in users}
    assert ids == {1, 2, 3}


async def test_concurrent_fetch_fails_if_any_id_invalid():
    with pytest.raises(ValueError):
        await fetch_users_concurrently([1, -1, 3])


# ---------------------------------------------------------------------------
# 3. Mocking async functions with AsyncMock
#    Regular MagicMock can't be awaited — use AsyncMock for async callables.
# ---------------------------------------------------------------------------

async def test_async_mock_is_awaitable():
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value={"data": "result"})

    response = await call_external_api(mock_client, "/users/1")

    assert response["data"] == "result"
    mock_client.get.assert_awaited_once_with("/users/1")


async def test_async_mock_side_effect():
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=ConnectionError("timeout"))

    with pytest.raises(ConnectionError, match="timeout"):
        await call_external_api(mock_client, "/users/1")


# ---------------------------------------------------------------------------
# 4. patch for async functions
# ---------------------------------------------------------------------------

async def load_config() -> dict:
    return {"debug": False, "max_connections": 10}


async def start_app() -> str:
    config = await load_config()
    if config["debug"]:
        return "debug mode"
    return "production mode"


async def test_patch_async_dependency():
    with patch(
        "test_01_async_functions.load_config",
        new=AsyncMock(return_value={"debug": True, "max_connections": 5}),
    ):
        result = await start_app()

    assert result == "debug mode"


# ---------------------------------------------------------------------------
# 5. Async context managers
# ---------------------------------------------------------------------------

class AsyncResource:
    def __init__(self, name: str):
        self.name = name
        self.closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.closed = True

    async def read(self) -> str:
        return f"data from {self.name}"


async def test_async_context_manager():
    async with AsyncResource("db") as resource:
        data = await resource.read()

    assert data == "data from db"
    assert resource.closed is True


async def test_async_context_manager_cleanup_on_exception():
    resource = AsyncResource("conn")
    try:
        async with resource:
            raise ValueError("simulated error")
    except ValueError:
        pass

    assert resource.closed is True
