"""
Transfer all rows from the SQLite library.db into the PostgreSQL library database.

Strategy:
  1. Read every row from SQLite using the existing SQLAlchemy models.
  2. Insert them into Postgres using the same models but a different engine.
  3. After inserting, reset Postgres sequences so auto-increment continues
     from the right value (SQLite doesn't use sequences, Postgres does).
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from models import Base, Author, Book

SQLITE_URL = "sqlite:///./library.db"
POSTGRES_URL = "postgresql+psycopg2://alex@localhost/library"

sqlite_engine = create_engine(SQLITE_URL)
pg_engine = create_engine(POSTGRES_URL)

SqliteSession = sessionmaker(bind=sqlite_engine)
PgSession = sessionmaker(bind=pg_engine)

sqlite_session = SqliteSession()
pg_session = PgSession()

# ── 1. Read from SQLite ────────────────────────────────────────────────────────

authors = sqlite_session.query(Author).all()
books = sqlite_session.query(Book).all()
print(f"Found {len(authors)} authors and {len(books)} books in SQLite.")

# ── 2. Insert into Postgres ────────────────────────────────────────────────────
# We detach the ORM objects from their original session so we can re-add them
# to the Postgres session.  expire_on_commit=False keeps attribute values
# accessible after the original session commits/closes.

sqlite_session.expunge_all()  # detach all objects from the SQLite session

for author in authors:
    pg_session.merge(author)  # merge inserts OR updates based on primary key

for book in books:
    pg_session.merge(book)

pg_session.commit()
print("Data inserted into PostgreSQL.")

# ── 3. Reset sequences ─────────────────────────────────────────────────────────
# PostgreSQL auto-increment sequences track the "next" ID separately from the
# actual data.  If we INSERT rows with explicit IDs (as we did above), the
# sequence is NOT advanced — the next INSERT without an explicit ID would try
# ID 1 again and fail with a unique-constraint error.
#
# setval(<sequence>, max_id) fixes this.

with pg_engine.connect() as conn:
    for table, col in [("authors", "id"), ("books", "id")]:
        conn.execute(text(
            f"SELECT setval(pg_get_serial_sequence('{table}', '{col}'), "
            f"COALESCE(MAX({col}), 0) + 1, false) FROM {table}"
        ))
    conn.commit()

print("Postgres sequences reset — auto-increment will continue from the right value.")

# ── 4. Verify ──────────────────────────────────────────────────────────────────

pg_authors = pg_session.query(Author).all()
pg_books = pg_session.query(Book).all()
print(f"\nVerification — Postgres now has {len(pg_authors)} authors and {len(pg_books)} books:")
for author in pg_authors:
    author_books = [b.title for b in pg_books if b.author_id == author.id]
    print(f"  {author.name} ({author.birth_year}): {author_books}")

sqlite_session.close()
pg_session.close()
