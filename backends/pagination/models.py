from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
    published_at = Column(DateTime, server_default=func.now(), nullable=False)
    view_count = Column(Integer, default=0, nullable=False)

    comments = relationship("Comment", back_populates="article", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    author = Column(String(100), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    article = relationship("Article", back_populates="comments")
