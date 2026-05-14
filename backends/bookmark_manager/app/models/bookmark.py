from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.links import BookmarkTagLink

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.tag import Tag
    from app.models.user import User


class Bookmark(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(max_length=2048)
    title: str = Field(max_length=300)
    description: str | None = Field(default=None, max_length=1000)
    favorite: bool = False
    click_count: int = Field(default=0, nullable=False)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    category_id: int | None = Field(
        default=None, foreign_key="category.id", index=True, ondelete="SET NULL"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: "User" = Relationship(back_populates="bookmarks")
    category: Optional["Category"] = Relationship(back_populates="bookmarks")
    tags: list["Tag"] = Relationship(
        back_populates="bookmarks", link_model=BookmarkTagLink
    )
