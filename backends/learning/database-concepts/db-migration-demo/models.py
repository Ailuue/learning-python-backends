from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_year = Column(Integer)

    books = relationship("Book", back_populates="author", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Author(name={self.name!r}, birth_year={self.birth_year})>"


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("authors.id"), nullable=False
    )
    published_year: Mapped[int] = mapped_column(Integer)
    genre: Mapped[str] = mapped_column(String(50))
    summary: Mapped[str] = mapped_column(Text)

    author = relationship("Author", back_populates="books")

    def __repr__(self):
        return f"<Book(title={self.title!r}, author_id={self.author_id})>"
