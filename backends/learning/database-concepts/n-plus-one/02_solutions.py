"""
Loading Strategies: selectinload and joinedload
===============================================
SQLAlchemy provides two primary strategies for eager-loading relationships,
each generating different SQL.

selectinload
  Runs a second SELECT with an IN clause covering all parent IDs collected
  from the first query. Always exactly 2 queries regardless of N.

    SELECT * FROM authors
    SELECT * FROM books WHERE books.author_id IN (1, 2, 3, 4, 5)

  The IN list is built from the IDs returned by the first query, so the
  second query fetches all related rows in one round-trip.

joinedload
  Adds a LEFT OUTER JOIN to the original query, fetching parents and
  children together in a single round-trip.

    SELECT authors.*, books.*
    FROM   authors
           LEFT OUTER JOIN books ON authors.id = books.author_id

  Because a JOIN multiplies rows (one per book per author), SQLAlchemy
  must deduplicate the result. You call .unique() on the result to get
  one Author object per row. See 03_tradeoffs.py for when this matters.

Nesting
  Both strategies can be chained for multi-level loading:

    selectinload(Author.books).selectinload(Book.tags)
    → 3 queries total: authors, then books IN (...), then book_tags IN (...)
"""

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

import db


def demo_selectinload() -> None:
    print("=" * 60)
    print("selectinload — 2 queries, IN clause")
    print("=" * 60)

    session = db.get_session()

    print("Code:  select(Author).options(selectinload(Author.books))\n")

    with db.query_log(show_sql=True):
        authors = session.scalars(
            select(db.Author).options(selectinload(db.Author.books))
        ).all()
        # Accessing .books fires no additional queries — already loaded
        result = [(a.name, [b.title for b in a.books]) for a in authors]

    print(f"  Loaded {len(result)} authors and all their books.\n")
    print(
        "  Query 1: SELECT authors  (fetches all authors, collects their IDs)\n"
        "  Query 2: SELECT books WHERE author_id IN (1,2,3,4,5)\n"
        "           (fetches all books in one shot using the collected IDs)\n"
        "  No matter how many authors exist, it's always exactly 2 queries.\n"
    )

    session.close()


def demo_joinedload() -> None:
    print("=" * 60)
    print("joinedload — 1 query, LEFT OUTER JOIN")
    print("=" * 60)

    session = db.get_session()

    print("Code:  select(Author).options(joinedload(Author.books))\n")

    with db.query_log(show_sql=True):
        authors = session.scalars(
            select(db.Author).options(joinedload(db.Author.books))
        ).unique().all()
        # .unique() is required with joinedload — the JOIN produces duplicate
        # Author rows (one per book) which SQLAlchemy needs to collapse
        result = [(a.name, [b.title for b in a.books]) for a in authors]

    print(f"  Loaded {len(result)} authors and all their books.\n")
    print(
        "  1 query with a LEFT OUTER JOIN — parents and children arrive together.\n"
        "  .unique() deduplicates: the JOIN returns one row per book, so an\n"
        "  author with 4 books appears 4 times in the raw result set.\n"
        "  See 03_tradeoffs.py for when that row multiplication is a problem.\n"
    )

    session.close()


def demo_selectinload_nested() -> None:
    print("=" * 60)
    print("selectinload nested — authors → books → tags  (3 queries)")
    print("=" * 60)

    session = db.get_session()

    print("Code:  selectinload(Author.books).selectinload(Book.tags)\n")

    with db.query_log(show_sql=True):
        authors = session.scalars(
            select(db.Author).options(
                selectinload(db.Author.books).selectinload(db.Book.tags)
            )
        ).all()
        _ = [
            (a.name, [(b.title, [t.name for t in b.tags]) for b in a.books])
            for a in authors
        ]

    print(
        "  Query 1: SELECT authors\n"
        "  Query 2: SELECT books WHERE author_id IN (...)\n"
        "  Query 3: SELECT tags JOIN book_tags WHERE book_id IN (...)\n\n"
        "  Compare this to the nested lazy-load from 01_n_plus_one.py\n"
        "  which fired 26 queries for the same data. This fires 3.\n"
    )

    session.close()


def demo_side_by_side() -> None:
    print("=" * 60)
    print("SIDE BY SIDE — lazy vs selectinload vs joinedload")
    print("=" * 60)

    strategies = [
        ("lazy (default)",  lambda: select(db.Author)),
        ("selectinload",    lambda: select(db.Author).options(selectinload(db.Author.books))),
        ("joinedload",      lambda: select(db.Author).options(joinedload(db.Author.books))),
    ]

    for label, build_query in strategies:
        session = db.get_session()
        with db.query_log() as queries:
            if "joinedload" in label:
                authors = session.scalars(build_query()).unique().all()
            else:
                authors = session.scalars(build_query()).all()
            for author in authors:
                _ = author.books
        session.close()
        n = len(queries)
        print(f"  {label:<18}  {n} quer{'y' if n == 1 else 'ies'}")

    print()


def main() -> None:
    demo_selectinload()
    demo_joinedload()
    demo_selectinload_nested()
    demo_side_by_side()


if __name__ == "__main__":
    main()
