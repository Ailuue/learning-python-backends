"""
Rate Limiting as FastAPI Middleware
=====================================
Wraps the sliding window algorithm in a Starlette middleware so it applies
automatically to every request without touching individual route handlers.

    Request arrives
        │
        ▼
    ┌─────────────────────┐
    │  RateLimitMiddleware │
    │  extract identifier  │  (client IP from X-Forwarded-For or host)
    │  check sliding window│
    └─────────┬───────────┘
              │
         ┌────┴────┐
         │ allowed │  yes → forward to route handler → normal response
         └────┬────┘
              │ no
              ▼
         HTTP 429  Too Many Requests
         Retry-After: <seconds until window resets>

Per-route limits
    Different endpoints often need different limits. The middleware checks a
    route-to-config map and falls back to a global default. This keeps
    per-route logic out of the route handlers themselves.

Headers returned on every response
    X-RateLimit-Limit:     max requests per window
    X-RateLimit-Remaining: requests left in current window
    X-RateLimit-Reset:     epoch seconds when the current window expires

Run:
    uvicorn 04_middleware:app --reload

Test:
    # Normal request
    curl -i http://localhost:8000/

    # Hit the strict /search limit (3 req / 30s) quickly:
    for i in $(seq 1 5); do curl -si http://localhost:8000/search | head -5; done

    # Watch the rate limit headers on a regular endpoint:
    for i in $(seq 1 12); do
        curl -si http://localhost:8000/ | grep -E "HTTP|X-Rate|Retry"
    done
"""

import time
import uuid
from dataclasses import dataclass

import redis_rl
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()


# ---------------------------------------------------------------------------
# Sliding window implementation (same logic as 02_sliding_window.py)
# ---------------------------------------------------------------------------

_LUA = """
local key    = KEYS[1]
local now    = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local member = ARGV[3]

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
redis.call('ZADD', key, now, member)
local count = redis.call('ZCARD', key)
redis.call('EXPIRE', key, window)
return count
"""
_script = redis_rl.client.register_script(_LUA)


def check_rate_limit(identifier: str, limit: int, window: int) -> tuple[bool, int]:
    """Returns (allowed, current_count)."""
    key = f"rl:sliding:{identifier}"
    member = f"{time.time()}:{uuid.uuid4()}"
    count = int(redis_rl.sync(_script(keys=[key], args=[time.time(), window, member])))
    return count <= limit, count


# ---------------------------------------------------------------------------
# Route-specific limit configuration
# ---------------------------------------------------------------------------

@dataclass
class RateConfig:
    limit: int
    window: int   # seconds


ROUTE_LIMITS: dict[str, RateConfig] = {
    "/search": RateConfig(limit=3, window=30),   # strict — expensive endpoint
    "/upload": RateConfig(limit=5, window=60),   # moderate
}
DEFAULT_LIMIT = RateConfig(limit=10, window=10)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        config = ROUTE_LIMITS.get(request.url.path, DEFAULT_LIMIT)

        # Use X-Forwarded-For if behind a proxy, otherwise fall back to host.
        # request.client is None when there is no peer address (a unix socket, or
        # Starlette's TestClient), so don't reach through it unguarded.
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "unknown"

        identifier = f"{client_ip}:{request.url.path}"
        allowed, count = check_rate_limit(identifier, config.limit, config.window)

        remaining = max(0, config.limit - count)
        reset_at = int(time.time()) + config.window

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "retry_after": config.window,
                },
                headers={
                    "Retry-After": str(config.window),
                    "X-RateLimit-Limit": str(config.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                },
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(config.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)
        return response


app.add_middleware(RateLimitMiddleware)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"message": "Hello! Default limit: 10 req / 10s."}


@app.get("/search")
async def search(q: str = ""):
    return {"results": [], "query": q, "note": "Strict limit: 3 req / 30s."}


@app.get("/upload")
async def upload():
    return {"note": "Moderate limit: 5 req / 60s."}
