from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    birth_year = Column(Integer)

    books = relationship("Book", back_populates="author", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Author(name={self.name!r}, birth_year={self.birth_year})>"


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    published_year = Column(Integer)
    genre = Column(String(50))
    summary = Column(Text)

    author = relationship("Author", back_populates="books")

    def __repr__(self):
        return f"<Book(title={self.title!r}, author_id={self.author_id})>"
