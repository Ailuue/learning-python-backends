import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

load_dotenv()

_url = (
    f"postgresql+psycopg2://{os.getenv('DB_USER', 'alex')}"
    f":{os.getenv('DB_PASSWORD', '')}"
    f"@{os.getenv('DB_HOST', 'localhost')}"
    f":{os.getenv('DB_PORT', '5432')}"
    f"/{os.getenv('DB_NAME', 'n_plus_one_demo')}"
)

# echo=False — we capture queries ourselves so we can count and display them
engine = create_engine(_url, echo=False)
SessionFactory = sessionmaker(bind=engine)


# ── Models ─────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


book_tags = Table(
    "book_tags",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.id"), primary_key=True),
    Column("tag_id",  Integer, ForeignKey("tags.id"),  primary_key=True),
)


class Author(Base):
    __tablename__ = "authors"

    id:         Mapped[int] = mapped_column(primary_key=True)
    name:       Mapped[str] = mapped_column(String(100))
    birth_year: Mapped[int] = mapped_column(Integer)

    books: Mapped[list["Book"]] = relationship(back_populates="author")

    def __repr__(self) -> str:
        return f"Author({self.name!r})"


class Book(Base):
    __tablename__ = "books"

    id:             Mapped[int] = mapped_column(primary_key=True)
    title:          Mapped[str] = mapped_column(String(200))
    author_id:      Mapped[int] = mapped_column(ForeignKey("authors.id"))
    genre:          Mapped[str] = mapped_column(String(50))

    author: Mapped["Author"] = relationship(back_populates="books")
    tags:   Mapped[list["Tag"]] = relationship(secondary=book_tags, back_populates="books")

    def __repr__(self) -> str:
        return f"Book({self.title!r})"


class Tag(Base):
    __tablename__ = "tags"

    id:   Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    books: Mapped[list["Book"]] = relationship(secondary=book_tags, back_populates="tags")

    def __repr__(self) -> str:
        return f"Tag({self.name!r})"


# ── Session helper ─────────────────────────────────────────────────────────────

def get_session() -> Session:
    return SessionFactory()


# ── Query counter / logger ─────────────────────────────────────────────────────
#
# Hooks into SQLAlchemy's before_cursor_execute event to intercept every SQL
# statement sent to the database. This lets us count and display queries without
# enabling SQLAlchemy's full echo mode (which is noisy with internal bookkeeping
# queries).

@contextmanager
def query_log(show_sql: bool = False):
    """
    Context manager that counts every SQL statement fired within the block.

    Usage:
        with query_log(show_sql=True) as queries:
            authors = session.scalars(select(Author)).all()
            for author in authors:
                _ = author.books  # lazy loads fire here
    """
    queries: list[str] = []

    def _listener(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement.strip())

    event.listen(engine, "before_cursor_execute", _listener)
    try:
        yield queries
    finally:
        event.remove(engine, "before_cursor_execute", _listener)
        n = len(queries)
        print(f"  → {n} quer{'y' if n == 1 else 'ies'} fired")
        if show_sql:
            for i, sql in enumerate(queries, 1):
                # Collapse whitespace and truncate for readability
                flat = " ".join(sql.split())
                print(f"     [{i}] {flat[:200]}")
        print()


# ── Schema & seed ──────────────────────────────────────────────────────────────

def setup() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    session = get_session()

    tags = [Tag(name=n) for n in [
        "classic", "dystopian", "sci-fi", "literary", "short-stories",
        "philosophy", "adventure", "romance",
    ]]
    session.add_all(tags)
    session.flush()

    tag = {t.name: t for t in tags}

    authors_books = [
        (Author(name="George Orwell",       birth_year=1903), [
            ("Nineteen Eighty-Four",  "dystopian",   [tag["dystopian"], tag["classic"], tag["literary"]]),
            ("Animal Farm",           "fable",       [tag["classic"], tag["literary"]]),
            ("Homage to Catalonia",   "non-fiction", [tag["literary"]]),
            ("Keep the Aspidistra",   "literary",    [tag["literary"]]),
        ]),
        (Author(name="Ursula K. Le Guin",   birth_year=1929), [
            ("The Left Hand of Darkness", "sci-fi",  [tag["sci-fi"], tag["classic"]]),
            ("The Dispossessed",          "sci-fi",  [tag["sci-fi"], tag["philosophy"]]),
            ("A Wizard of Earthsea",      "fantasy", [tag["adventure"]]),
            ("The Ones Who Walk Away",    "sci-fi",  [tag["short-stories"], tag["philosophy"]]),
        ]),
        (Author(name="Franz Kafka",          birth_year=1883), [
            ("The Trial",             "literary",    [tag["literary"], tag["classic"]]),
            ("The Metamorphosis",     "literary",    [tag["short-stories"], tag["classic"]]),
            ("The Castle",            "literary",    [tag["literary"]]),
            ("In the Penal Colony",   "short story", [tag["short-stories"]]),
        ]),
        (Author(name="Octavia Butler",       birth_year=1947), [
            ("Kindred",               "sci-fi",      [tag["sci-fi"], tag["classic"]]),
            ("Parable of the Sower",  "sci-fi",      [tag["sci-fi"], tag["dystopian"]]),
            ("Dawn",                  "sci-fi",      [tag["sci-fi"], tag["adventure"]]),
            ("Bloodchild",            "sci-fi",      [tag["short-stories"], tag["sci-fi"]]),
        ]),
        (Author(name="Fyodor Dostoevsky",    birth_year=1821), [
            ("Crime and Punishment",  "literary",    [tag["classic"], tag["literary"]]),
            ("The Brothers Karamazov","literary",    [tag["classic"], tag["philosophy"]]),
            ("The Idiot",             "literary",    [tag["classic"], tag["literary"]]),
            ("Notes from Underground","literary",    [tag["short-stories"], tag["philosophy"]]),
        ]),
    ]

    for author, books in authors_books:
        session.add(author)
        session.flush()
        for title, genre, book_tags_list in books:
            book = Book(title=title, author_id=author.id, genre=genre)
            book.tags = book_tags_list
            session.add(book)

    session.commit()
    session.close()
    print(f"Seeded {len(authors_books)} authors, "
          f"{sum(len(b) for _, b in authors_books)} books, "
          f"{len(tags)} tags.\n")
