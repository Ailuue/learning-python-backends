from datetime import datetime, timezone
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.bookmark import Bookmark


class Category(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("name", "user_id", name="uq_category_name_user"),)

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(min_length=1, max_length=100, index=True)
    description: str | None = Field(default=None, max_length=500)
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: ClassVar = relationship(
        "User",
        back_populates="categories",
        foreign_keys="[Category.user_id]",
    )
    bookmarks: list["Bookmark"] = Relationship(back_populates="category")
