import logging
import re

import httpx
from sqlmodel import Session

from app.celery_app import celery_app
from app.database import engine
from app.models import Bookmark
from app.redis_client import get_redis

logger = logging.getLogger(__name__)

_TITLE_PATTERN = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
CLICK_KEY_PREFIX = "bookmark_clicks:"


@celery_app.task(
    name="app.tasks.fetch_bookmark_metadata",
    autoretry_for=(httpx.RequestError,),
    retry_kwargs={"max_retries": 2},
    retry_backoff=True,
)
def fetch_bookmark_metadata(bookmark_id: int, url: str) -> None:
    """Fetch the <title> at `url` and overwrite the bookmark's title if it's still the URL."""
    try:
        with httpx.Client(timeout=5.0, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": "BookmarkManager/1.0"})
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.warning("HTTP %s fetching metadata for bookmark %s", e.response.status_code, bookmark_id)
        return

    match = _TITLE_PATTERN.search(response.text)
    if not match:
        logger.info("No <title> found for bookmark %s (%s)", bookmark_id, url)
        return

    title = match.group(1).strip()[:300]
    with Session(engine) as session:
        bookmark = session.get(Bookmark, bookmark_id)
        if bookmark and bookmark.title == bookmark.url:
            bookmark.title = title
            session.add(bookmark)
            session.commit()
            logger.info("Updated bookmark %s with title: %s", bookmark_id, title)


@celery_app.task(name="app.tasks.flush_bookmark_clicks")
def flush_bookmark_clicks() -> dict:
    """Drain `bookmark_clicks:*` counters from Redis and apply them to the DB.

    Scheduled every 10 minutes by Celery Beat. This is the write-behind flush.

    Trade-off: if Redis crashes between flushes, we lose up to 10 minutes of
    clicks. Acceptable for analytics-style data; not for anything safety-critical.
    """
    r = get_redis()
    pending: dict[int, int] = {}

    # SCAN (not KEYS) so we don't block Redis on big keyspaces.
    # GETDEL atomically reads and removes the key, so any clicks that arrive
    # *between* SCAN and GETDEL are still captured in this batch. Clicks that
    # arrive after GETDEL create a fresh key and roll into the next window.
    for key in r.scan_iter(match=f"{CLICK_KEY_PREFIX}*"):
        # decode_responses=True at the client level means sync Redis returns str,
        # but redis-py's type stubs use a generic Awaitable-or-T union. Narrow
        # explicitly so the conversions below typecheck.
        if not isinstance(key, str):
            continue
        value = r.getdel(key)
        if not isinstance(value, str):
            continue
        try:
            bookmark_id = int(key.split(":", 1)[1])
            count = int(value)
        except (ValueError, IndexError):
            logger.warning("Skipping malformed click key: %s", key)
            continue
        if count > 0:
            pending[bookmark_id] = count

    if not pending:
        logger.info("flush_bookmark_clicks: nothing to flush")
        return {"flushed": 0, "bookmarks": 0}

    total = 0
    with Session(engine) as session:
        for bookmark_id, count in pending.items():
            bookmark = session.get(Bookmark, bookmark_id)
            if bookmark is None:
                logger.warning(
                    "Bookmark %s no longer exists; dropping %s clicks",
                    bookmark_id,
                    count,
                )
                continue
            bookmark.click_count += count
            session.add(bookmark)
            total += count
        session.commit()

    logger.info(
        "flush_bookmark_clicks: applied %s clicks across %s bookmarks",
        total,
        len(pending),
    )
    return {"flushed": total, "bookmarks": len(pending)}
