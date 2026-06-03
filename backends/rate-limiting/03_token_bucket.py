"""
Token Bucket Rate Limiting
===========================
A bucket holds tokens up to a maximum capacity. Tokens refill at a fixed
rate. Each request costs one token. If the bucket is empty, the request
is denied.

    capacity = 10 tokens   rate = 2 tokens/second

    t=0  [■■■■■■■■■■]  10 tokens  → request allowed (9 left)
    t=0  [■■■■■■■■■ ]   9 tokens  → request allowed (8 left)
    ...burst of 10 requests in <1s, all allowed...
    t=0  [          ]   0 tokens  → DENY
    t=1  [■■        ]   2 tokens  → request allowed (1 left) — refilled 2
    t=2  [■■■       ]   3 tokens  → request allowed (2 left) — refilled 2

Token bucket vs sliding window
    Sliding window: enforces an exact count per rolling time period.
      "No more than 5 requests per 10 seconds, ever."
    Token bucket:   allows burst up to capacity, then enforces a sustained rate.
      "You can burst 10 requests instantly, but long-term you average 2/s."

    Use token bucket for APIs where occasional bursts are legitimate
    (a user triggering a bulk import) but sustained hammering is not.

Redis implementation
    Two keys per identifier:
      rl:bucket:{id}:tokens  — current token count (float)
      rl:bucket:{id}:last    — timestamp of last refill (float)

    On each request:
      1. Compute elapsed = now - last_refill
      2. new_tokens = min(capacity, stored_tokens + elapsed * rate)
      3. If new_tokens >= 1: subtract 1, allow
      4. Else: deny

    Lua script makes steps 1-4 atomic. Without it, two concurrent requests
    could both read the same token count, both decide "allowed", and both
    subtract — double-spending a single token.

Run:
    python 03_token_bucket.py
"""

import time

import redis_rl

CAPACITY = 10      # maximum tokens in the bucket
RATE = 2.0         # tokens added per second
COST = 1           # tokens consumed per request

# Lua script — read-modify-write is atomic
_LUA = """
local tokens_key = KEYS[1]
local last_key   = KEYS[2]
local capacity   = tonumber(ARGV[1])
local rate       = tonumber(ARGV[2])
local cost       = tonumber(ARGV[3])
local now        = tonumber(ARGV[4])
local ttl        = tonumber(ARGV[5])

local last   = tonumber(redis.call('GET', last_key))  or now
local tokens = tonumber(redis.call('GET', tokens_key)) or capacity

-- Refill based on time elapsed since last request
local elapsed   = math.max(0, now - last)
local new_tokens = math.min(capacity, tokens + elapsed * rate)

if new_tokens >= cost then
    redis.call('SET', tokens_key, new_tokens - cost)
    redis.call('SET', last_key, now)
    redis.call('EXPIRE', tokens_key, ttl)
    redis.call('EXPIRE', last_key, ttl)
    return {1, math.floor(new_tokens - cost)}   -- {allowed, tokens_remaining}
else
    redis.call('SET', tokens_key, new_tokens)
    redis.call('SET', last_key, now)
    redis.call('EXPIRE', tokens_key, ttl)
    redis.call('EXPIRE', last_key, ttl)
    return {0, 0}
end
"""
_script = redis_rl.client.register_script(_LUA)

# Keys expire after bucket would fully refill from empty — no orphan keys.
_TTL = int(CAPACITY / RATE) + 5


def is_allowed(identifier: str, now: float | None = None) -> tuple[bool, int]:
    """Returns (allowed, tokens_remaining_after_this_request)."""
    if now is None:
        now = time.time()
    tokens_key = f"rl:bucket:{identifier}:tokens"
    last_key = f"rl:bucket:{identifier}:last"
    result = _script(keys=[tokens_key, last_key],
                     args=[CAPACITY, RATE, COST, now, _TTL])
    return bool(int(result[0])), int(result[1])


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def make_requests(identifier: str, timestamps: list[float], label: str):
    print(f"\n  {label}")
    for i, ts in enumerate(timestamps, 1):
        allowed, tokens = is_allowed(identifier, now=ts)
        status = "ALLOW" if allowed else "DENY "
        print(f"    req {i:2d}  t={ts - timestamps[0]:4.1f}s  [{status}]  tokens after: {tokens}")


def main():
    redis_rl.flush()

    print("=== Token Bucket Rate Limiting ===")
    print(f"    capacity={CAPACITY} tokens  rate={RATE} tokens/s  cost={COST}/request\n")

    base = 1000.0

    # ------------------------------------------------------------------
    print("--- Burst: 10 rapid requests exhaust the bucket ---")
    redis_rl.flush()
    times = [base + i * 0.05 for i in range(13)]   # 50ms apart, 13 requests
    make_requests("user:1", times, "13 requests in 0.6s (bucket holds 10)")

    # ------------------------------------------------------------------
    print("\n--- Refill: after burst, tokens replenish at 2/s ---")
    redis_rl.flush()
    # Burst 10, then wait 3s, then burst again
    burst1 = [base + i * 0.05 for i in range(10)]
    # At t=3s, rate=2/s means 6 new tokens → 6 more requests succeed
    burst2 = [base + 3.0 + i * 0.05 for i in range(8)]
    make_requests("user:1", burst1 + burst2, "burst-wait-burst pattern")

    # ------------------------------------------------------------------
    print("\n--- Sustained load: steady 1 req/s, always allowed ---")
    redis_rl.flush()
    times = [base + i * 1.0 for i in range(12)]    # exactly at the refill rate
    make_requests("user:1", times, "1 request per second (rate=2/s, plenty of tokens)")


if __name__ == "__main__":
    main()
