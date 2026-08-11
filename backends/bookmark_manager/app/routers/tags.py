import logging

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.dependencies import CurrentUserDep, SessionDep
from app.models import Tag
from app.schemas.tag import TagCreate, TagPublic

router = APIRouter(prefix="/tags", tags=["tags"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=TagPublic, status_code=status.HTTP_201_CREATED)
def create_tag(tag_in: TagCreate, user: CurrentUserDep, session: SessionDep) -> Tag:
    existing = session.exec(
        select(Tag).where((Tag.name == tag_in.name) & (Tag.user_id == user.id))
    ).first()
    if existing:
        return existing
    tag = Tag(name=tag_in.name, user_id=user.pk)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.get("/", response_model=list[TagPublic])
def list_tags(user: CurrentUserDep, session: SessionDep) -> list[Tag]:
    return list(
        session.exec(select(Tag).where(Tag.user_id == user.id).order_by(Tag.name)).all()
    )


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int, user: CurrentUserDep, session: SessionDep) -> None:
    tag = session.get(Tag, tag_id)
    if not tag or tag.user_id != user.id:
        raise HTTPException(status_code=404, detail="Tag not found")
    session.delete(tag)
    session.commit()
    logger.info("User %s deleted tag %s", user.username, tag_id)
