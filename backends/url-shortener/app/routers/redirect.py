from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import cache
from app.database import get_db
from app.models import URL
from app.tasks import increment_click

router = APIRouter(tags=["redirect"])


@router.get("/{short_code}", include_in_schema=False)
async def redirect_to_url(
    short_code: str,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    # Hot path: Redis cache hit — no DB query, click counted asynchronously via Celery
    cached_url = await cache.get(short_code)
    if cached_url:
        increment_click.delay(short_code)
        return RedirectResponse(url=cached_url, status_code=301)

    result = await db.execute(
        select(URL).where(URL.short_code == short_code, URL.is_active.is_(True))
    )
    url_row = result.scalar_one_or_none()

    if url_row is None:
        raise HTTPException(status_code=404, detail="Short URL not found")

    if url_row.expires_at and url_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="This short URL has expired")

    await cache.set(short_code, url_row.original_url)
    increment_click.delay(short_code)

    return RedirectResponse(url=url_row.original_url, status_code=301)
