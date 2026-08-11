import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, status
from sqlmodel import Session, col, select

from app.dependencies import CurrentUserDep, SessionDep
from app.models import Bookmark, Category, Tag
from app.rate_limit import limiter
from app.redis_client import get_redis
from app.schemas.bookmark import BookmarkCreate, BookmarkPublic, BookmarkUpdate
from app.tasks import fetch_bookmark_metadata


CLICK_KEY_PREFIX = "bookmark_clicks:"

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])
logger = logging.getLogger(__name__)


def _get_or_create_tag(session: Session, user_id: int, name: str) -> Tag:
    tag = session.exec(
        select(Tag).where((Tag.name == name) & (Tag.user_id == user_id))
    ).first()
    if tag is None:
        tag = Tag(name=name, user_id=user_id)
        session.add(tag)
        session.flush()
    return tag


def _validate_category(session: Session, user_id: int, category_id: int | None) -> None:
    if category_id is None:
        return
    category = session.get(Category, category_id)
    if not category or category.user_id != user_id:
        raise HTTPException(status_code=404, detail="Category not found")


@router.post("/", response_model=BookmarkPublic, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_bookmark(
    request: Request,
    bookmark_in: BookmarkCreate,
    user: CurrentUserDep,
    session: SessionDep,
) -> Bookmark:
    # An authenticated user is always persisted, so its primary key is set.
    assert user.id is not None
    _validate_category(session, user.pk, bookmark_in.category_id)

    url_str = str(bookmark_in.url)
    bookmark = Bookmark(
        url=url_str,
        title=bookmark_in.title or url_str,
        description=bookmark_in.description,
        favorite=bookmark_in.favorite,
        category_id=bookmark_in.category_id,
        user_id=user.id,
    )

    # Add the bookmark to the session before linking tags. Looking up each tag
    # triggers an autoflush, and the tag<->bookmark association only proceeds if
    # the bookmark is already known to the session.
    session.add(bookmark)
    for tag_name in bookmark_in.tags:
        bookmark.tags.append(_get_or_create_tag(session, user.pk, tag_name))

    session.commit()
    session.refresh(bookmark)

    if not bookmark_in.title:
        fetch_bookmark_metadata.delay(bookmark.id, url_str)

    logger.info("User %s created bookmark %s", user.username, bookmark.id)
    return bookmark


@router.get("/", response_model=list[BookmarkPublic])
def list_bookmarks(
    user: CurrentUserDep,
    session: SessionDep,
    category_id: int | None = None,
    favorite: bool | None = None,
    tag: str | None = None,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 50,
) -> list[Bookmark]:
    query = select(Bookmark).where(Bookmark.user_id == user.id)
    if category_id is not None:
        query = query.where(Bookmark.category_id == category_id)
    if favorite is not None:
        query = query.where(Bookmark.favorite == favorite)
    if tag is not None:
        query = query.join(col(Bookmark.tags)).where(Tag.name == tag)
    query = query.order_by(col(Bookmark.created_at).desc()).offset(offset).limit(limit)
    return list(session.exec(query).all())


@router.get("/{bookmark_id}", response_model=BookmarkPublic)
def read_bookmark(
    bookmark_id: int, user: CurrentUserDep, session: SessionDep
) -> Bookmark:
    bookmark = session.get(Bookmark, bookmark_id)
    if not bookmark or bookmark.user_id != user.id:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return bookmark


@router.patch("/{bookmark_id}", response_model=BookmarkPublic)
def update_bookmark(
    bookmark_id: int,
    bookmark_in: BookmarkUpdate,
    user: CurrentUserDep,
    session: SessionDep,
) -> Bookmark:
    bookmark = session.get(Bookmark, bookmark_id)
    if not bookmark or bookmark.user_id != user.id:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    update_data = bookmark_in.model_dump(exclude_unset=True, exclude={"tags"})
    if "url" in update_data:
        update_data["url"] = str(update_data["url"])
    if "category_id" in update_data:
        _validate_category(session, user.pk, update_data["category_id"])

    for field, value in update_data.items():
        setattr(bookmark, field, value)
    bookmark.updated_at = datetime.now(timezone.utc)

    if bookmark_in.tags is not None:
        bookmark.tags.clear()
        for tag_name in bookmark_in.tags:
            bookmark.tags.append(_get_or_create_tag(session, user.pk, tag_name))

    session.add(bookmark)
    session.commit()
    session.refresh(bookmark)
    logger.info("User %s updated bookmark %s", user.username, bookmark.id)
    return bookmark


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(
    bookmark_id: int, user: CurrentUserDep, session: SessionDep
) -> None:
    bookmark = session.get(Bookmark, bookmark_id)
    if not bookmark or bookmark.user_id != user.id:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    session.delete(bookmark)
    session.commit()
    logger.info("User %s deleted bookmark %s", user.username, bookmark_id)


@router.post("/{bookmark_id}/click", status_code=status.HTTP_204_NO_CONTENT)
def record_click(
    bookmark_id: int, user: CurrentUserDep, session: SessionDep
) -> None:
    """Increment the click counter for a bookmark in Redis.

    The actual DB column is updated every 10 minutes by the
    `flush_bookmark_clicks` Celery Beat task — a write-behind cache.
    """
    bookmark = session.get(Bookmark, bookmark_id)
    if not bookmark or bookmark.user_id != user.id:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    get_redis().incr(f"{CLICK_KEY_PREFIX}{bookmark_id}")
