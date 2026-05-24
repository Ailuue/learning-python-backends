"""
The N+1 Problem
===============
When you load a list of N parent objects and then access a relationship
on each one, SQLAlchemy's default lazy loading fires one SQL query per
parent — giving you N extra queries on top of the original one.

  1 query  — SELECT the list of authors
  N queries — SELECT books for author 1, author 2, ..., author N

That's N+1 queries total. With 5 authors it's 6 queries. With 500 it's 501.
The problem is silent: the code looks fine, the results are correct, but
the number of round-trips to the database grows linearly with your data.

How SQLAlchemy lazy loading works
----------------------------------
By default, every relationship is lazy-loaded. The relationship attribute
(e.g. author.books) holds a proxy object. The first time you access it,
SQLAlchemy fires a SELECT to populate it. This happens automatically and
invisibly — there's no indication in the code that a query is being made.

The query_log() context manager in db.py hooks into SQLAlchemy's
before_cursor_execute event so we can count and display every query fired.
"""

from sqlalchemy import select

import db


def demo_lazy_one_level() -> None:
    print("=" * 60)
    print("LAZY LOADING — authors → books  (1 + N queries)")
    print("=" * 60)

    session = db.get_session()

    print("Code:  authors = session.scalars(select(Author)).all()")
    print("       for author in authors:")
    print("           print(author.name, author.books)  ← triggers load\n")

    with db.query_log(show_sql=True) as queries:
        authors = session.scalars(select(db.Author)).all()

        # Accessing author.books inside the loop triggers a SELECT per author
        for author in authors:
            book_titles = [b.title for b in author.books]

    print(
        f"  5 authors loaded, each with ~4 books.\n"
        f"  Query 1 fetches all authors.\n"
        f"  Queries 2–{len(queries)} each fetch books for one author.\n"
        f"  This is the N+1 pattern: 1 + N queries, one round-trip per row.\n"
    )

    session.close()


def demo_lazy_two_levels() -> None:
    print("=" * 60)
    print("NESTED N+1 — authors → books → tags  (1 + N + N×M queries)")
    print("=" * 60)

    session = db.get_session()

    print("Code:  for author in authors:")
    print("           for book in author.books:   ← N queries")
    print("               print(book.tags)         ← M queries per book\n")

    with db.query_log(show_sql=True) as queries:
        authors = session.scalars(select(db.Author)).all()
        for author in authors:
            for book in author.books:
                _ = [t.name for t in book.tags]

    n_authors  = 5
    n_books    = 20
    n_tag_sets = 20
    print(
        f"  1 query for authors\n"
        f"  + {n_authors} queries for books (one per author)\n"
        f"  + {n_tag_sets} queries for tags (one per book)\n"
        f"  = {len(queries)} total queries to render what amounts to a simple nested list.\n"
        f"  Add more authors and books and this scales to hundreds or thousands.\n"
    )

    session.close()


def demo_the_silent_part() -> None:
    print("=" * 60)
    print("WHY IT'S SILENT — the code gives no hint")
    print("=" * 60)

    print(
        "These two snippets look identical. One fires 6 queries; one fires 1.\n"
    )
    print(
        "  # Version A — 6 queries (N+1)\n"
        "  authors = session.scalars(select(Author)).all()\n"
        "  for author in authors:\n"
        "      print(author.books)          # ← lazy query fires here\n"
    )
    print(
        "  # Version B — 2 queries (eager)\n"
        "  authors = session.scalars(\n"
        "      select(Author).options(selectinload(Author.books))\n"
        "  ).all()\n"
        "  for author in authors:\n"
        "      print(author.books)          # ← already loaded, no query\n"
    )
    print(
        "Without the query counter, you'd never know Version A was a problem\n"
        "until it showed up as slow pages in production.\n"
        "See 02_solutions.py for how to fix it.\n"
    )


def main() -> None:
    db.setup()
    demo_lazy_one_level()
    demo_lazy_two_levels()
    demo_the_silent_part()


if __name__ == "__main__":
    main()
