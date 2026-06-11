"""
Shared Celery application instance.

Every concept file imports `app` from here so they all use the same
broker (Redis) and result backend (also Redis).

Celery architecture at a glance:
  Producer  →  Broker (Redis)  →  Worker  →  Result Backend (Redis)
  (your code enqueues)         (picks up)  (stores return value)
"""

from celery import Celery

app = Celery(
    "celery_concepts",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",  # db 1 keeps results separate from tasks
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # How long to keep results in Redis before expiry (10 min for demo purposes)
    result_expires=600,
)
