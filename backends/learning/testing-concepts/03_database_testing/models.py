from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id:         Mapped[int]      = mapped_column(primary_key=True)
    username:   Mapped[str]      = mapped_column(String(50), unique=True, nullable=False)
    email:      Mapped[str]      = mapped_column(String(200), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    posts: Mapped[list["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username!r})"


class Post(Base):
    __tablename__ = "posts"

    id:         Mapped[int]      = mapped_column(primary_key=True)
    title:      Mapped[str]      = mapped_column(String(200), nullable=False)
    body:       Mapped[str]      = mapped_column(Text, nullable=False)
    published:  Mapped[bool]     = mapped_column(default=False, nullable=False)
    user_id:    Mapped[int]      = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    author: Mapped["User"] = relationship(back_populates="posts")

    def __repr__(self) -> str:
        return f"Post(id={self.id}, title={self.title!r})"
