from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "async_users"

    id:         Mapped[int]      = mapped_column(primary_key=True)
    username:   Mapped[str]      = mapped_column(String(50), unique=True, nullable=False)
    email:      Mapped[str]      = mapped_column(String(200), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    posts: Mapped[list["Post"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )


class Post(Base):
    __tablename__ = "async_posts"

    id:        Mapped[int]  = mapped_column(primary_key=True)
    title:     Mapped[str]  = mapped_column(String(200), nullable=False)
    body:      Mapped[str]  = mapped_column(Text, nullable=False)
    published: Mapped[bool] = mapped_column(default=False, nullable=False)
    user_id:   Mapped[int]  = mapped_column(ForeignKey("async_users.id"), nullable=False)

    author: Mapped["User"] = relationship(back_populates="posts")
