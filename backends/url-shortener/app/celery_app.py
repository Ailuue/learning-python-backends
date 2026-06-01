from celery import Celery

from app.config import settings

celery = Celery(
    "url_shortener",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,       # Re-queue task if worker crashes mid-execution
    worker_prefetch_multiplier=4,
)
