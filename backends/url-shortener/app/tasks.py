from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session

from app.celery_app import celery
from app.config import settings
from app.models import URL

# Celery workers are separate processes — they don't share the FastAPI async event loop.
# A sync engine + psycopg2 is the right tool here: simple, no asyncio overhead.
_sync_engine = None


def _get_engine():
    global _sync_engine
    if _sync_engine is None:
        sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
        _sync_engine = create_engine(sync_url, pool_size=5, max_overflow=10, pool_pre_ping=True)
    return _sync_engine


@celery.task(name="tasks.increment_click")
def increment_click(short_code: str) -> None:
    with Session(_get_engine()) as db:
        db.execute(
            update(URL)
            .where(URL.short_code == short_code)
            .values(click_count=URL.click_count + 1)
        )
        db.commit()
