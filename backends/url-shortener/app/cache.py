import redis.asyncio as aioredis

from app.config import settings

_redis: aioredis.Redis | None = None

_KEY_PREFIX = "url:"


async def init() -> None:
    global _redis
    _redis = aioredis.from_url(settings.redis_url, decode_responses=True)


async def close() -> None:
    if _redis:
        await _redis.aclose()


def _key(short_code: str) -> str:
    return f"{_KEY_PREFIX}{short_code}"


async def get(short_code: str) -> str | None:
    assert _redis is not None
    return await _redis.get(_key(short_code))


async def set(short_code: str, original_url: str) -> None:
    assert _redis is not None
    await _redis.setex(_key(short_code), settings.cache_ttl, original_url)


async def invalidate(short_code: str) -> None:
    assert _redis is not None
    await _redis.delete(_key(short_code))


async def stats() -> dict:
    assert _redis is not None
    info = await _redis.info("stats")
    return {
        "keyspace_hits": info.get("keyspace_hits"),
        "keyspace_misses": info.get("keyspace_misses"),
    }
