from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.bookmark import Bookmark
    from app.models.category import Category
    from app.models.tag import Tag


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    username: str = Field(unique=True, index=True, min_length=3, max_length=50)
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    bookmarks: list["Bookmark"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    categories: list["Category"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    tags: list["Tag"] = Relationship(back_populates="user", cascade_delete=True)
