from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# nomic-embed-text produces 768-dimensional vectors
EMBEDDING_DIM = 768


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    # Mapped[...] + mapped_column is the SQLAlchemy 2.0 declarative style. The
    # generated table is identical to bare Column(), but attribute access on an
    # instance is typed as the Python value rather than as Column[...].
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(username={self.username!r})>"


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # NULL until embed_comments.py is run
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIM), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="comments")

    def __repr__(self):
        return f"<Comment(id={self.id}, user_id={self.user_id})>"
