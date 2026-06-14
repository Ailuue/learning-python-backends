"""
Concept 02 — Task States & the Result Backend

Every Celery task moves through a state machine:

  PENDING → STARTED → SUCCESS
                    ↘ FAILURE
                    ↘ RETRY     (on the way back to STARTED)
                    ↘ REVOKED   (task was cancelled)

PENDING is the default state for any task ID — even one that doesn't exist.
That's why you must always store the task ID yourself if you want to poll later.

The result backend (Redis db 1 in our setup) stores:
  - The final return value (on SUCCESS)
  - The exception + traceback (on FAILURE)
  - Intermediate custom state (if you call update_state() inside the task)

Custom states are useful for long-running tasks that need to report progress
back to a polling client (e.g. a frontend progress bar).

HOW TO RUN THIS FILE:
  Terminal 1:  docker compose up
  Terminal 2:  celery -A 02_task_states worker --loglevel=info
  Terminal 3:  python 02_task_states.py
"""

import time
from celery.exceptions import Ignore
from celery_app import app


# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------

@app.task(bind=True)
def long_running_job(self, steps: int):
    """
    bind=True gives the task access to `self` (the task instance).
    We use self.update_state() to push custom progress updates that
    a caller can read by polling AsyncResult.info.
    """
    for i in range(steps):
        time.sleep(0.5)
        self.update_state(
            state="PROGRESS",
            meta={"current": i + 1, "total": steps, "pct": round((i + 1) / steps * 100)},
        )
    return {"message": "done", "steps_completed": steps}


@app.task
def always_fails():
    raise ValueError("This task always raises an exception.")


@app.task(bind=True)
def manual_success(self):
    """
    Sometimes you want to set a custom terminal state instead of SUCCESS.
    Raise Ignore() to prevent Celery from overwriting your update_state() call.
    """
    self.update_state(state="COMPLETE", meta={"note": "custom terminal state"})
    raise Ignore()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def poll_progress(promise, label: str):
    """Poll a task every 0.5s, printing state transitions."""
    print(f"\n   Polling '{label}' (id={promise.id[:8]}...):")
    seen_states = set()
    while not promise.ready():
        state = promise.state
        if state not in seen_states:
            info = promise.info if promise.info else {}
            print(f"     state={state}  info={info}")
            seen_states.add(state)
        time.sleep(0.5)
    return promise


def main():
    print("=" * 60)
    print("CONCEPT 02 — Task States & Result Backend")
    print("=" * 60)

    # --- Normal lifecycle ---
    print("\n1. Normal lifecycle (PENDING → STARTED → SUCCESS):")
    p = long_running_job.delay(4)
    p = poll_progress(p, "long_running_job")
    print(f"   Final state: {p.state}")
    print(f"   Result:      {p.result}")

    # --- Failure state ---
    print("\n2. Failure state:")
    p2 = always_fails.delay()
    try:
        p2.get(timeout=5)
    except Exception as exc:
        print(f"   get() raised: {type(exc).__name__}: {exc}")
    print(f"   State: {p2.state}")
    # p2.result holds the exception object after FAILURE
    print(f"   .result (exception): {p2.result}")
    # Traceback is also stored:
    print(f"   .traceback (first line): {p2.traceback.splitlines()[0] if p2.traceback else None}")

    # --- Custom terminal state ---
    print("\n3. Custom terminal state via Ignore():")
    p3 = manual_success.delay()
    # propagate=False means get() won't re-raise Ignore
    p3.get(timeout=5, propagate=False)
    print(f"   State: {p3.state}")
    print(f"   Info:  {p3.info}")

    # --- PENDING for unknown ID ---
    print("\n4. Unknown task ID is always PENDING:")
    from celery.result import AsyncResult
    ghost = AsyncResult("00000000-0000-0000-0000-000000000000", app=app)
    print(f"   State: {ghost.state}")  # PENDING — not 'not found'


if __name__ == "__main__":
    main()
