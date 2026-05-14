from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.models.links import BookmarkTagLink

if TYPE_CHECKING:
    from app.models.bookmark import Bookmark
    from app.models.user import User


class Tag(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("name", "user_id", name="uq_tag_name_user"),)

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(min_length=1, max_length=50, index=True)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")

    user: "User" = Relationship(back_populates="tags")
    bookmarks: list["Bookmark"] = Relationship(
        back_populates="tags", link_model=BookmarkTagLink
    )
