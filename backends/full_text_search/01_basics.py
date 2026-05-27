"""
Full-Text Search Basics: tsvector and tsquery
==============================================
PostgreSQL FTS works on two core types:

  tsvector — a preprocessed, searchable representation of a document.
             Text is broken into lexemes: normalised word forms with stop
             words removed. Each lexeme records the positions it appears at.

             to_tsvector('english', 'The foxes are quickly running') produces:
               'fox':2 'quick':4 'run':5
             'The' and 'are' are stop words (dropped).
             'foxes' → 'fox', 'quickly' → 'quick', 'running' → 'run' (stemmed).

  tsquery  — a search expression of lexemes with Boolean operators:
               & (AND)   | (OR)   ! (NOT)   <-> (followed by / phrase)
             The query is also normalised: 'Databases' becomes 'databas'.

  @@       — the match operator. Returns true when a tsvector satisfies
             a tsquery.

             to_tsvector('english', text) @@ to_tsquery('english', query)

Three query-building functions:

  to_tsquery('english', 'database & index')
    Operators (&, |, !) must be explicit. Raw words are normalised.
    Raises an error if you pass plain prose with spaces.

  plainto_tsquery('english', 'database index')
    Treats spaces as AND. Safe to use with arbitrary user input.
    'database index' → 'databas & index'

  websearch_to_tsquery('english', '"full text" OR index -slow')
    Web-search syntax: quoted phrases, OR, leading minus for NOT.
    The safest choice for a user-facing search box.

  phraseto_tsquery('english', 'full text search')
    All words must appear in order and adjacent.
    'full text search' → 'full' <-> 'text' <-> 'search'
"""

import db

SETUP = db.SETUP
SEED  = db.SEED


def demo_tsvector_anatomy() -> None:
    print("=" * 60)
    print("TSVECTOR — what text looks like after processing")
    print("=" * 60)

    with db.cursor() as cur:
        print("Input:   'The foxes are quickly running over lazy dogs'\n")
        cur.execute(
            "SELECT to_tsvector('english', "
            "'The foxes are quickly running over lazy dogs')"
        )
        print(f"tsvector: {cur.fetchone()[0]}\n")

        print(
            "Observations:\n"
            "  • 'The', 'are', 'over' — English stop words, dropped entirely\n"
            "  • 'foxes'  → 'fox'    (stemmed)\n"
            "  • 'quickly'→ 'quick'  (stemmed)\n"
            "  • 'running'→ 'run'    (stemmed)\n"
            "  • 'lazy'   → 'lazi'   (stemmed — Porter stemmer artifact)\n"
            "  • Numbers after ':' are token positions in the original text\n"
        )

        print("Input:   'databases are indexed by the database engine'\n")
        cur.execute(
            "SELECT to_tsvector('english', "
            "'databases are indexed by the database engine')"
        )
        print(f"tsvector: {cur.fetchone()[0]}\n")
        print(
            "  • 'databases' and 'database' both normalise to 'databas'\n"
            "  • A search for 'database' matches both words in a document\n"
        )


def demo_stop_words() -> None:
    print("=" * 60)
    print("STOP WORDS — common words that carry no search value")
    print("=" * 60)

    phrases = [
        "the quick brown fox",
        "a very important thing",
        "this is the way",
        "PostgreSQL is a powerful system",
    ]

    with db.cursor() as cur:
        for phrase in phrases:
            cur.execute("SELECT to_tsvector('english', %s)", (phrase,))
            vec = cur.fetchone()[0]
            print(f"  Input:   '{phrase}'")
            print(f"  Lexemes: {vec or '(empty — all stop words)'}\n")

    print(
        "  Stop words are defined per language configuration.\n"
        "  to_tsvector('english', ...) uses the English stop word list.\n"
        "  'is', 'a', 'the', 'this', 'very' are all English stop words.\n"
    )


def demo_query_functions() -> None:
    print("=" * 60)
    print("QUERY FUNCTIONS — four ways to build a tsquery")
    print("=" * 60)

    with db.cursor() as cur:
        examples = [
            ("to_tsquery",        "to_tsquery('english', 'database & index')"),
            ("plainto_tsquery",   "plainto_tsquery('english', 'database index')"),
            ("websearch_to_tsquery (phrase)", "websearch_to_tsquery('english', '\"full text search\"')"),
            ("websearch_to_tsquery (OR/NOT)", "websearch_to_tsquery('english', 'database OR index -slow')"),
            ("phraseto_tsquery",  "phraseto_tsquery('english', 'full text search')"),
        ]
        for label, expr in examples:
            cur.execute(f"SELECT {expr}")
            print(f"  {label}:\n    {cur.fetchone()[0]}\n")

    print(
        "  <->  means 'immediately followed by' (phrase / adjacency operator)\n"
        "  &    means AND — both lexemes must appear\n"
        "  |    means OR  — either lexeme must appear\n"
        "  !    means NOT — lexeme must not appear\n"
    )


def demo_match_operator() -> None:
    print("=" * 60)
    print("@@ OPERATOR — does this document match the query?")
    print("=" * 60)

    with db.cursor() as cur:
        tests = [
            ("PostgreSQL has powerful full-text search features",  "full-text search"),
            ("Python is great for data science and machine learning", "full-text search"),
            ("Running queries on a database requires an index",     "running query"),
            ("She sells sea shells by the sea shore",               "sea shell"),
        ]
        print(f"  {'Document':<52}  {'Query':<20}  Match")
        print(f"  {'-'*52}  {'-'*20}  -----")
        for doc, query in tests:
            cur.execute(
                "SELECT to_tsvector('english', %s) @@ plainto_tsquery('english', %s)",
                (doc, query),
            )
            match = "✓" if cur.fetchone()[0] else "✗"
            print(f"  {doc[:50]:<52}  {query:<20}  {match}")
        print()
        print(
            "  'Running queries' matches 'running query' because both 'running'\n"
            "  and 'queries' stem to 'run' and 'queri' — same lexemes as 'running query'.\n"
        )


def demo_searching_articles() -> None:
    print("=" * 60)
    print("SEARCHING ARTICLES — basic @@ query against the table")
    print("=" * 60)

    with db.cursor() as cur:
        cur.execute(db.SETUP)
        cur.execute(db.SEED)

        queries = [
            ("database",          "plainto_tsquery('english', 'database')"),
            ("index performance", "plainto_tsquery('english', 'index performance')"),
            ("python ORM",        "plainto_tsquery('english', 'python ORM')"),
        ]
        for label, tsquery in queries:
            print(f"  Search: '{label}'")
            db.print_table(
                cur,
                f"""
                SELECT id, title, author
                FROM   articles
                WHERE  to_tsvector('english', title || ' ' || body)
                       @@ {tsquery}
                ORDER  BY id
                """,
                ["id", "title", "author"],
            )

    print(
        "  Notice: no ranking yet — results are in insertion order.\n"
        "  Also notice: to_tsvector() is called on every row for every query.\n"
        "  See 03_indexes.py for why that's expensive and how to fix it.\n"
    )


def main() -> None:
    demo_tsvector_anatomy()
    demo_stop_words()
    demo_query_functions()
    demo_match_operator()
    demo_searching_articles()


if __name__ == "__main__":
    main()
