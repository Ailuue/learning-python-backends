"""
Concept 01 — Defining and calling tasks

A Celery task is just a regular Python function decorated with @app.task.
You can call it in three ways:

  add(2, 3)           → runs RIGHT NOW in the current process (no Celery involved)
  add.delay(2, 3)     → sends to the broker; a worker picks it up asynchronously
  add.apply_async(    → same as delay() but with extra options (countdown, eta, etc.)
      args=[2, 3],
      countdown=10,
  )

delay() returns an AsyncResult. You can use it to poll for the result, but be
careful — blocking on get() in a web handler defeats the purpose of async tasks.

HOW TO RUN THIS FILE:
  Terminal 1 (broker):  docker compose up
  Terminal 2 (worker):  celery -A 01_basic_tasks worker --loglevel=info
  Terminal 3 (demo):    python 01_basic_tasks.py
"""

import time
from celery_app import app


# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------

@app.task
def add(x, y):
    return x + y


@app.task
def slow_add(x, y):
    """Simulates a slow task (e.g. hitting an external API)."""
    time.sleep(3)
    return x + y


@app.task
def send_welcome_email(user_email: str):
    """
    Simulates sending an email.
    In a real app this would call SendGrid / SES / SMTP.
    """
    time.sleep(1)
    print(f"[task] Sent welcome email to {user_email}")
    return {"status": "sent", "to": user_email}


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CONCEPT 01 — Basic Tasks")
    print("=" * 60)

    # --- Synchronous call (no broker needed, useful for tests) ---
    print("\n1. Direct call (synchronous, no worker):")
    result = add(10, 20)
    print(f"   add(10, 20) = {result}")

    # --- Async call via delay() ---
    print("\n2. Async call via delay():")
    promise = add.delay(10, 20)
    print(f"   Task ID: {promise.id}")
    print(f"   Status before get(): {promise.status}")

    # get() blocks until the worker finishes and returns the result.
    # timeout= prevents hanging forever if the worker is down.
    result = promise.get(timeout=10)
    print(f"   Result: {result}")
    print(f"   Status after get(): {promise.status}")

    # --- apply_async with options ---
    print("\n3. apply_async with countdown (runs after 5 seconds):")
    promise2 = slow_add.apply_async(args=[7, 3], countdown=5)
    print(f"   Task ID: {promise2.id}")
    print("   Waiting for result (will take ~8s total: 5s delay + 3s work)...")
    result2 = promise2.get(timeout=15)
    print(f"   Result: {result2}")

    # --- Fire-and-forget (no get()) ---
    print("\n4. Fire-and-forget (email send, we don't wait):")
    send_welcome_email.delay("alex@example.com")
    print("   Task enqueued. Worker will process it — we moved on immediately.")


if __name__ == "__main__":
    main()
