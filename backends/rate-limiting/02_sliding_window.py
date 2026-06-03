"""
Sliding Window Rate Limiting
=============================
Instead of snapping to fixed boundaries, the window moves with time.
At every request, check: how many requests occurred in the last N seconds?

    time ──────────────────────────────────────────────────────▶
                     [     sliding window     ]
                     │   now - 60s       now  │
                     └────────────────────────┘
                     only requests inside this range are counted

Redis implementation (sorted set)
    key = "rl:sliding:{identifier}"
    ZREMRANGEBYSCORE key 0 (now - window)    ← evict expired entries
    ZADD key now "{now}:{uuid}"              ← record this request
    count = ZCARD key                        ← count requests in window
    EXPIRE key window                        ← clean up the key eventually
    if count > limit: 429

Each member in the sorted set is a request timestamp (score) with a unique
member string. The score lets Redis efficiently remove entries older than the
window using ZREMRANGEBYSCORE.

Memory trade-off:
    Fixed window stores one integer per user.
    Sliding window stores one entry per request per user.
    At 100 req/min limit with 10,000 users that's 1M entries — still fine
    for Redis, but worth knowing.

Boundary burst — does NOT exist here:
    The window always covers [now - window_size, now]. A burst at the
    boundary is visible because those requests are still inside the window
    when the next requests arrive.

Run:
    python 02_sliding_window.py
"""

import time
import uuid

import redis_rl

LIMIT = 5
WINDOW = 10   # seconds

# Lua script — all four commands run atomically to avoid races
_LUA = """
local key      = KEYS[1]
local now      = tonumber(ARGV[1])
local window   = tonumber(ARGV[2])
local member   = ARGV[3]
local limit    = tonumber(ARGV[4])

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
redis.call('ZADD', key, now, member)
local count = redis.call('ZCARD', key)
redis.call('EXPIRE', key, window)
return count
"""
_script = redis_rl.client.register_script(_LUA)


def is_allowed(identifier: str, now: float | None = None) -> tuple[bool, int]:
    """Returns (allowed, current_count_in_window)."""
    if now is None:
        now = time.time()
    key = f"rl:sliding:{identifier}"
    member = f"{now}:{uuid.uuid4()}"
    count = int(_script(keys=[key], args=[now, WINDOW, member, LIMIT]))
    return count <= LIMIT, count


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def make_requests(identifier: str, timestamps: list[float], label: str):
    print(f"\n  {label}")
    for i, ts in enumerate(timestamps, 1):
        allowed, count = is_allowed(identifier, now=ts)
        status = "ALLOW" if allowed else "DENY "
        print(f"    req {i:2d}  t={ts:.1f}  [{status}]  window count: {count}/{LIMIT}")


def main():
    redis_rl.flush()

    print("=== Sliding Window Rate Limiting ===")
    print(f"    limit={LIMIT} requests per {WINDOW}s rolling window\n")

    base = 1000.0   # arbitrary fixed base so output is deterministic

    # ------------------------------------------------------------------
    print("--- Normal traffic: 5 requests spread over the window ---")
    redis_rl.flush()
    times = [base + i * 2 for i in range(5)]    # one every 2 seconds
    make_requests("user:1", times, "5 requests, 2s apart")

    # ------------------------------------------------------------------
    print("\n--- 7 rapid requests: first 5 allowed, then 2 denied ---")
    redis_rl.flush()
    times = [base + i * 0.1 for i in range(7)]   # 100ms apart
    make_requests("user:1", times, "7 requests within 1 second")

    # ------------------------------------------------------------------
    print("\n--- Boundary burst: 5 requests near end of window, 5 at start of next ---")
    print("    Fixed window allowed all 10. Sliding window catches the burst.")
    redis_rl.flush()
    # 5 requests at t=9 (end of a hypothetical 10s window)
    # 5 requests at t=11 (start of next window, but only 2s later)
    times = (
        [base + 9 + i * 0.1 for i in range(5)]   # t≈9.0–9.4
        + [base + 11 + i * 0.1 for i in range(5)] # t≈11.0–11.4
    )
    make_requests("user:1", times, "5 at t≈9s, 5 at t≈11s (2s gap)")

    # ------------------------------------------------------------------
    print("\n--- Old requests expire: window slides, allowing new ones ---")
    redis_rl.flush()
    # 5 requests at t=0, then 3 more at t=12 (first 3 of the original 5 have aged out)
    times = (
        [base + i for i in range(5)]                # t=0–4
        + [base + WINDOW + 1 + i for i in range(3)] # t=11–13 (first entries gone)
    )
    make_requests("user:1", times, "5 requests, wait for window to slide, 3 more")


if __name__ == "__main__":
    main()
