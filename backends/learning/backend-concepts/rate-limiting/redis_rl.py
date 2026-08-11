"""
Shared Redis client and helpers for the rate-limiting demos.

Key naming convention:
  rl:fixed:{identifier}:{window_ts}   — fixed window counter
  rl:sliding:{identifier}             — sorted set of request timestamps
  rl:bucket:{identifier}:tokens       — token bucket current level
  rl:bucket:{identifier}:last         — token bucket last refill timestamp
"""

import os
from collections.abc import Awaitable
from typing import Any, cast

import redis
from dotenv import load_dotenv

load_dotenv()

client: redis.Redis = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    decode_responses=True,
)


def sync(value: "Awaitable[Any] | Any") -> Any:
    """
    Narrow a redis reply to its synchronous form.

    redis-py annotates every command (and registered Lua script) as
    ResponseT = Awaitable[Any] | Any, because the sync and async clients share one
    command mixin. `client` is the sync one, so the Awaitable arm never occurs.
    """
    return cast(Any, value)


def flush() -> None:
    """Wipe rate-limit keys. Only used at the top of each demo."""
    for key in client.scan_iter("rl:*"):
        client.delete(key)
