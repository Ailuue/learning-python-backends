"""Lazy Redis client used by the JWT blocklist (and anywhere else that needs it).

A module-level singleton with `get_redis()` / `set_redis()` lets tests swap in
`fakeredis` without monkey-patching every import site.
"""

import redis

from app.config import get_settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        settings = get_settings()
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def set_redis(client: redis.Redis) -> None:
    """For testing: inject a fake Redis client."""
    global _client
    _client = client
