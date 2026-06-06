"""
Shared Redis client and helpers for the rate-limiting demos.

Key naming convention:
  rl:fixed:{identifier}:{window_ts}   — fixed window counter
  rl:sliding:{identifier}             — sorted set of request timestamps
  rl:bucket:{identifier}:tokens       — token bucket current level
  rl:bucket:{identifier}:last         — token bucket last refill timestamp
"""

import os

import redis
from dotenv import load_dotenv

load_dotenv()

client: redis.Redis = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    decode_responses=True,
)


def flush() -> None:
    """Wipe rate-limit keys. Only used at the top of each demo."""
    for key in client.scan_iter("rl:*"):
        client.delete(key)
