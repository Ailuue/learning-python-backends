"""
When to Use Each Strategy
=========================
selectinload and joinedload solve the same problem differently.
Neither is universally better — the right choice depends on the
cardinality of the relationship and what else the query is doing.

joinedload is best for:
  • many-to-one / one-to-one relationships (e.g. book → author)
    No row multiplication because there's at most one related row.
  • Small collections where a single round-trip matters more than
    the slight overhead of deduplication.

selectinload is best for:
  • one-to-many / many-to-many collections (e.g. author → books)
    The JOIN multiplies rows; selectinload avoids that entirely.
  • Paginated queries — a JOIN changes the row count, which breaks
    LIMIT/OFFSET. selectinload runs as a separate query so pagination
    is unaffected.

contains_eager:
  • When your query already has an explicit JOIN (e.g. for filtering),
    use contains_eager to tell SQLAlchemy to populate the relationship
    from that existing join rather than issuing another query.
    Trying to joinedload when you've already joined will double-join.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import contains_eager, joinedload, selectinload

import db


def demo_row_multiplication() -> None:
    print("=" * 60)
    print("ROW MULTIPLICATION — why joinedload hurts on collections")
    print("=" * 60)

    session = db.get_session()

    # Count raw rows returned by the JOIN before deduplication
    raw_rows = session.execute(
        select(func.count()).select_from(
            select(db.Author, db.Book)
            .join(db.Book, db.Author.id == db.Book.author_id)
            .subquery()
        )
    ).scalar()

    author_count = session.scalar(select(func.count()).select_from(db.Author))
    book_count   = session.scalar(select(func.count()).select_from(db.Book))

    print(f"  Authors in database: {author_count}")
    print(f"  Books in database:   {book_count}")
    print(f"  Rows returned by JOIN: {raw_rows}  (one row per author-book pair)\n")

    print(
        "  joinedload with 1 query returns {r} rows over the wire.\n"
        "  SQLAlchemy's .unique() collapses them back to {a} Author objects.\n"
        "  The extra rows are discarded — but they were still transferred.\n\n"
        "  With selectinload:\n"
        "    Query 1 returns {a} rows  (authors)\n"
        "    Query 2 returns {b} rows  (books)\n"
        "    Total: {t} rows — exactly what you need, nothing wasted.\n".format(
            r=raw_rows, a=author_count, b=book_count, t=author_count + book_count
        )
    )

    session.close()


def demo_joinedload_on_many_to_one() -> None:
    print("=" * 60)
    print("joinedload on many-to-one — no row multiplication")
    print("=" * 60)

    session = db.get_session()

    print(
        "Loading books with their author (many-to-one).\n"
        "Each book has exactly one author, so the JOIN produces no extra rows.\n"
    )
    print("Code:  select(Book).options(joinedload(Book.author))\n")

    with db.query_log(show_sql=True):
        books = session.scalars(
            select(db.Book).options(joinedload(db.Book.author))
        ).unique().all()
        result = [(b.title, b.author.name) for b in books]

    print(
        f"  {len(result)} books loaded with their authors in 1 query.\n"
        "  No row multiplication: each book row joins to exactly 1 author row.\n"
        "  joinedload is the natural choice for many-to-one relationships.\n"
    )

    session.close()


def demo_pagination_with_selectinload() -> None:
    print("=" * 60)
    print("PAGINATION — selectinload is safe, joinedload breaks LIMIT")
    print("=" * 60)

    session = db.get_session()

    print(
        "Fetching page 1 of authors (limit 3), with their books.\n"
    )

    print("With selectinload (correct):")
    print("Code:  select(Author).options(selectinload(Author.books)).limit(3)\n")

    with db.query_log(show_sql=False):
        authors = session.scalars(
            select(db.Author)
            .options(selectinload(db.Author.books))
            .order_by(db.Author.id)
            .limit(3)
        ).all()
    print(f"  Got {len(authors)} authors: {[a.name for a in authors]}\n")

    print(
        "With joinedload (broken — LIMIT applies to JOIN rows, not authors):\n"
        "Code:  select(Author).options(joinedload(Author.books)).limit(3)\n"
        "\n"
        "  The JOIN produces 20 rows (5 authors × 4 books each).\n"
        "  LIMIT 3 cuts the first 3 JOIN rows — parts of the first author.\n"
        "  SQLAlchemy actually warns about this and works around it by\n"
        "  running a subquery, adding extra complexity and overhead.\n"
        "  selectinload has no such issue because LIMIT applies to the\n"
        "  first query (authors only) before the books query runs.\n"
    )

    session.close()


def demo_contains_eager() -> None:
    print("=" * 60)
    print("contains_eager — populate from an existing JOIN")
    print("=" * 60)

    session = db.get_session()

    print(
        "Goal: fetch only sci-fi books, but also load each book's author.\n"
        "We must JOIN authors to filter — contains_eager reuses that join\n"
        "to populate book.author without a second query.\n"
    )
    print(
        "Code:  select(Book)\n"
        "           .join(Book.author)\n"
        "           .where(Book.genre == 'sci-fi')\n"
        "           .options(contains_eager(Book.author))\n"
    )

    with db.query_log(show_sql=True):
        books = session.scalars(
            select(db.Book)
            .join(db.Book.author)
            .where(db.Book.genre == "sci-fi")
            .options(contains_eager(db.Book.author))
        ).all()
        result = [(b.title, b.author.name) for b in books]

    print(f"  {len(result)} sci-fi books loaded with authors in 1 query.\n")
    for title, author in result:
        print(f"    {title} — {author}")
    print()
    print(
        "  If you used joinedload here instead, SQLAlchemy would add a\n"
        "  second JOIN to the query — joining authors twice. contains_eager\n"
        "  tells SQLAlchemy: 'the JOIN is already there, read from it.'\n"
    )

    session.close()


def main() -> None:
    demo_row_multiplication()
    demo_joinedload_on_many_to_one()
    demo_pagination_with_selectinload()
    demo_contains_eager()


if __name__ == "__main__":
    main()
