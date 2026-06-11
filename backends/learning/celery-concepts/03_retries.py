"""
Concept 03 — Retries

Background tasks often hit transient failures: a third-party API is down,
a database connection times out, a rate limit kicks in. Retries let the
worker back off and try again automatically.

Two main approaches:

  A) autoretry_for — declarative, defined on the task decorator.
     Celery re-raises any listed exception after `countdown` seconds,
     up to `max_retries` times.

  B) self.retry() — manual, called inside the task body.
     Gives you full control: decide *whether* to retry, log context,
     compute a custom backoff, etc.

Exponential backoff pattern:
  retry 1 → wait 2s
  retry 2 → wait 4s
  retry 3 → wait 8s
  formula: 2 ** self.request.retries

Adding jitter (random extra seconds) prevents the "thundering herd" problem
where all retrying workers hit the service at the same time.

HOW TO RUN THIS FILE:
  Terminal 1:  docker compose up
  Terminal 2:  celery -A 03_retries worker --loglevel=info
  Terminal 3:  python 03_retries.py
"""

import random
import time
from celery_app import app


# ---------------------------------------------------------------------------
# Simulate an unreliable external service
# ---------------------------------------------------------------------------

_call_count = {}

def flaky_api_call(task_id: str, fail_times: int) -> str:
    """Fails the first `fail_times` calls, then succeeds."""
    _call_count[task_id] = _call_count.get(task_id, 0) + 1
    attempt = _call_count[task_id]
    if attempt <= fail_times:
        raise ConnectionError(f"API unavailable (attempt {attempt}/{fail_times + 1})")
    return f"API response (succeeded on attempt {attempt})"


# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------

@app.task(
    autoretry_for=(ConnectionError,),
    max_retries=4,
    retry_backoff=True,       # exponential backoff (2, 4, 8, 16 ... seconds)
    retry_backoff_max=30,     # cap the wait at 30s
    retry_jitter=True,        # add randomness to avoid thundering herd
)
def fetch_from_api_auto(payload: str):
    """
    autoretry_for handles everything automatically.
    Best when you just want simple retry-on-error with no custom logic.
    """
    return flaky_api_call("auto", fail_times=2)


@app.task(bind=True, max_retries=3)
def fetch_from_api_manual(self, payload: str, fail_times: int = 2):
    """
    Manual retry gives you control: log before retrying, compute custom
    countdown, conditionally give up, etc.
    """
    try:
        return flaky_api_call("manual", fail_times=fail_times)
    except ConnectionError as exc:
        attempt = self.request.retries + 1   # retries counts completed retries
        countdown = 2 ** attempt             # 2, 4, 8 seconds
        print(f"   [task] Attempt {attempt} failed. Retrying in {countdown}s...")
        # self.retry() raises a special exception that tells Celery to re-queue.
        # exc= preserves the original exception so it's available if all retries fail.
        raise self.retry(exc=exc, countdown=countdown)


@app.task(bind=True, max_retries=2)
def task_that_gives_up(self, fail_times: int = 5):
    """
    Sometimes retrying is pointless (e.g. invalid input, permanent 404).
    Call self.retry() without exc= and Celery will use MaxRetriesExceededError.
    Or just let the exception propagate normally — the task goes to FAILURE.
    """
    try:
        return flaky_api_call("givesup", fail_times=fail_times)
    except ConnectionError as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=1)
        # Exhausted retries — fall through to FAILURE state
        print("   [task] All retries exhausted. Giving up.")
        raise  # re-raise original exception → task enters FAILURE state


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CONCEPT 03 — Retries")
    print("=" * 60)

    # --- autoretry_for ---
    print("\n1. autoretry_for (declarative, fails 2x then succeeds):")
    print("   Watch the worker terminal for RETRY log entries.")
    p = fetch_from_api_auto.delay("data")
    result = p.get(timeout=60)
    print(f"   Final result: {result}")
    print(f"   State: {p.state}")

    # Reset shared counter for next demo
    _call_count.clear()

    # --- manual self.retry() ---
    print("\n2. Manual self.retry() (fails 2x then succeeds):")
    p2 = fetch_from_api_manual.delay("data", fail_times=2)
    result2 = p2.get(timeout=60)
    print(f"   Final result: {result2}")
    print(f"   State: {p2.state}")

    _call_count.clear()

    # --- task that exhausts retries ---
    print("\n3. Task that exhausts max_retries (fails 5x, only 2 retries allowed):")
    p3 = task_that_gives_up.delay(fail_times=5)
    try:
        p3.get(timeout=30)
    except Exception as exc:
        print(f"   get() raised: {type(exc).__name__}: {exc}")
    print(f"   State: {p3.state}")


if __name__ == "__main__":
    main()
