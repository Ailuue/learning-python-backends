from datetime import datetime, timezone
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.bookmark import Bookmark
    from app.models.tag import Tag


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    username: str = Field(unique=True, index=True, min_length=3, max_length=50)
    password_hash: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    default_category_id: int | None = Field(
        default=None, foreign_key="category.id", ondelete="SET NULL"
    )

    bookmarks: list["Bookmark"] = Relationship(back_populates="user", cascade_delete=True)
    # Two FK paths exist between User and Category (default_category_id → category.id
    # and category.user_id → user.id), so SQLModel's auto-detection is ambiguous.
    # Using SQLAlchemy's relationship() directly with explicit foreign_keys resolves it.
    categories: ClassVar = relationship(
        "Category",
        back_populates="user",
        foreign_keys="[Category.user_id]",
        cascade="all, delete-orphan",
    )
    tags: list["Tag"] = Relationship(back_populates="user", cascade_delete=True)

    @property
    def pk(self) -> int:
        """
        The primary key, typed non-Optional.

        `id` is `int | None` only because SQLModel assigns it on flush — a user
        loaded from the database always has one. Routes that pass the id into a
        foreign key should use this rather than spreading `assert` over call sites.
        """
        if self.id is None:
            raise RuntimeError("user has not been persisted yet")
        return self.id
