from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import cache
from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import URL, User
from app.schemas import URLCreate, URLListResponse, URLResponse, URLStats
from app.shortener import generate_short_code

router = APIRouter(prefix="/urls", tags=["urls"])

_MAX_RETRIES = 5


def _to_response(url: URL) -> URLResponse:
    return URLResponse(
        id=url.id,
        short_code=url.short_code,
        original_url=url.original_url,
        short_url=f"{settings.base_url}/{url.short_code}",
        created_at=url.created_at,
        expires_at=url.expires_at,
        click_count=url.click_count,
        is_active=url.is_active,
    )


@router.post("", response_model=URLResponse, status_code=201)
async def create_short_url(
    payload: URLCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> URLResponse:
    for _ in range(_MAX_RETRIES):
        short_code = payload.custom_code or generate_short_code()
        url = URL(
            short_code=short_code,
            original_url=payload.original_url,
            expires_at=payload.expires_at,
        )
        db.add(url)
        try:
            await db.commit()
            await db.refresh(url)
            return _to_response(url)
        except IntegrityError:
            await db.rollback()
            if payload.custom_code:
                raise HTTPException(status_code=409, detail="Custom code already taken")

    raise HTTPException(status_code=500, detail="Failed to generate a unique short code")


@router.get("", response_model=URLListResponse)
async def list_urls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> URLListResponse:
    offset = (page - 1) * page_size
    total = (await db.execute(select(func.count()).select_from(URL))).scalar_one()
    rows = (
        await db.execute(select(URL).order_by(URL.created_at.desc()).offset(offset).limit(page_size))
    ).scalars().all()

    return URLListResponse(
        items=[_to_response(u) for u in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{short_code}/stats", response_model=URLStats)
async def get_url_stats(short_code: str, db: AsyncSession = Depends(get_db)) -> URLStats:
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url = result.scalar_one_or_none()
    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return URLStats(
        short_code=url.short_code,
        original_url=url.original_url,
        click_count=url.click_count,
        created_at=url.created_at,
        expires_at=url.expires_at,
        is_active=url.is_active,
    )


@router.delete("/{short_code}", status_code=204)
async def deactivate_url(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url = result.scalar_one_or_none()
    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    url.is_active = False
    await db.commit()
    await cache.invalidate(short_code)
