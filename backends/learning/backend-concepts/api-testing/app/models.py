from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id:       Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email:    Mapped[str] = mapped_column(String(200), unique=True)

    posts: Mapped[list["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")


class Post(Base):
    __tablename__ = "posts"

    id:         Mapped[int]      = mapped_column(primary_key=True)
    user_id:    Mapped[int]      = mapped_column(ForeignKey("users.id"))
    title:      Mapped[str]      = mapped_column(String(200))
    body:       Mapped[str]      = mapped_column(Text)
    published:  Mapped[bool]     = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    author: Mapped["User"] = relationship(back_populates="posts")
