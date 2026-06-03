"""
Fixed Window Rate Limiting
===========================
The simplest algorithm. Divide time into discrete windows of equal size.
Count requests per identifier (user ID, IP) per window. Reject when the
count exceeds the limit.

    time ────────────────────────────────────────────────────────▶
         │  Window 1 (0–60s) │  Window 2 (60–120s) │
         │  [■■■■■     ]     │  [■           ]     │
         │  5/5 allowed      │  1/5 allowed        │

Redis implementation
    key   = "rl:fixed:{id}:{window_start}"
    INCR key              → current count
    if count == 1:
        EXPIRE key TTL    → start the clock on first request in window
    if count > limit: 429

Atomicity note:
    INCR and EXPIRE are two separate commands. If the process dies between
    them the key never expires — a stuck counter that permanently blocks the
    user. A Lua script runs both atomically on the Redis server and eliminates
    this race.

The boundary burst problem
    A client can make LIMIT requests at 00:59 and LIMIT more at 01:01.
    That's 2×LIMIT requests in a 2-second span, yet both windows see a
    clean count. Fixed windows cannot detect cross-boundary bursts.

    time ───────────────────────────────────────────────▶
         │  Window 1      │  Window 2      │
         │  [        ■■■■■│■■■■■          ]│
         │  5/5 OK        │  5/5 OK        │  ← 10 in 2 sec!

    The demo below makes this visible: watch requests 5–6 in the output.

Use fixed window when:
  • You need simple per-hour/per-day quota accounting (billing)
  • The boundary burst is acceptable or clients are trusted
  • Simplicity beats precision

Run:
    python 01_fixed_window.py
"""

import time

import redis_rl

LIMIT = 5
WINDOW = 10   # seconds (kept small so the demo runs fast)

# Lua script — INCR + conditional EXPIRE in a single atomic operation
_LUA = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""
_script = redis_rl.client.register_script(_LUA)


def window_start(now: float, window: int) -> int:
    """Floor timestamp to the current window boundary."""
    return int(now) // window * window


def is_allowed(identifier: str, now: float | None = None) -> tuple[bool, int]:
    """
    Returns (allowed, current_count).
    Pass `now` explicitly in tests to simulate specific timestamps.
    """
    if now is None:
        now = time.time()
    ws = window_start(now, WINDOW)
    key = f"rl:fixed:{identifier}:{ws}"
    count = int(_script(keys=[key], args=[WINDOW]))
    return count <= LIMIT, count


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def make_requests(identifier: str, n: int, now: float, label: str):
    print(f"\n  {label}")
    for i in range(1, n + 1):
        allowed, count = is_allowed(identifier, now=now + (i * 0.01))
        status = "ALLOW" if allowed else "DENY "
        print(f"    req {i:2d}  [{status}]  window count: {count}/{LIMIT}")


def main():
    redis_rl.flush()

    print("=== Fixed Window Rate Limiting ===")
    print(f"    limit={LIMIT} requests per {WINDOW}s window\n")

    # ------------------------------------------------------------------
    print("--- Normal traffic: 4 requests, well under limit ---")
    make_requests("user:1", 4, now=time.time(), label="4 requests in window 1")

    # ------------------------------------------------------------------
    print("\n--- Burst: 7 requests, 5 allowed then 2 denied ---")
    redis_rl.flush()
    make_requests("user:1", 7, now=time.time(), label="7 requests in window 1")

    # ------------------------------------------------------------------
    print("\n--- Boundary burst: 5 at end of window, 5 at start of next ---")
    print("    (10 requests in ~2 seconds — both windows report OK)")
    redis_rl.flush()
    base = time.time()
    # Put 5 requests 1 second before the next window boundary
    ws = window_start(base, WINDOW)
    near_end = ws + WINDOW - 1   # 1 second before boundary
    make_requests("user:1", 5, now=near_end,  label="5 requests at window end")
    make_requests("user:1", 5, now=ws + WINDOW, label="5 requests at window start (new window)")
    print("\n    → All 10 were allowed. Fixed window didn't see the burst.")
    print("      Sliding window (02) would have caught this.")


if __name__ == "__main__":
    main()
