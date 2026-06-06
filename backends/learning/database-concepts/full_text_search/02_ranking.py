"""
Ranking and Highlighting
========================
Matching documents tells you what is relevant; ranking tells you how
relevant. PostgreSQL provides two ranking functions and a snippet
generator.

ts_rank(tsvector, tsquery)
  Scores a document based on term frequency — how often the query
  terms appear. A document mentioning 'database' ten times scores
  higher than one mentioning it once.

ts_rank_cd(tsvector, tsquery)
  Cover density ranking. Also considers how close together the query
  terms appear in the document. 'database index' in adjacent sentences
  scores higher than the same words pages apart.
  cd = cover density.

setweight(tsvector, weight)
  Assigns a weight label (A, B, C, or D) to every lexeme in a tsvector.
  ts_rank uses these weights: A > B > C > D.
  Typical use: weight title lexemes as A, body lexemes as B.
  A document whose title contains the search term scores higher than
  one where only the body contains it.

ts_headline(config, document, query, [options])
  Returns a snippet of the original document with query terms
  highlighted in <b>...</b> tags. Does not operate on tsvector —
  it works on the raw text to preserve the original wording.

  Useful options:
    MaxWords=N       — max words in snippet (default 35)
    MinWords=N       — min words in snippet (default 15)
    StartSel=X       — opening highlight tag  (default <b>)
    StopSel=X        — closing highlight tag  (default </b>)
    HighlightAll=t   — highlight the whole document, not just a snippet
"""

import db


def demo_ts_rank() -> None:
    print("=" * 60)
    print("ts_rank — score by term frequency")
    print("=" * 60)

    with db.cursor() as cur:
        print("  Search: 'database'\n")
        db.print_table(
            cur,
            """
            SELECT id,
                   title,
                   round(ts_rank(
                       to_tsvector('english', title || ' ' || body),
                       plainto_tsquery('english', 'database')
                   )::numeric, 6) AS rank
            FROM   articles
            WHERE  to_tsvector('english', title || ' ' || body)
                   @@ plainto_tsquery('english', 'database')
            ORDER  BY rank DESC
            """,
            ["id", "title", "rank"],
            truncate=45,
        )

        print("  Search: 'search index'\n")
        db.print_table(
            cur,
            """
            SELECT id,
                   title,
                   round(ts_rank(
                       to_tsvector('english', title || ' ' || body),
                       plainto_tsquery('english', 'search index')
                   )::numeric, 6) AS rank
            FROM   articles
            WHERE  to_tsvector('english', title || ' ' || body)
                   @@ plainto_tsquery('english', 'search index')
            ORDER  BY rank DESC
            """,
            ["id", "title", "rank"],
            truncate=45,
        )

    print(
        "  Articles that mention the search term more often score higher.\n"
        "  The absolute score values are not meaningful on their own —\n"
        "  only relative ordering within a result set matters.\n"
    )


def demo_setweight() -> None:
    print("=" * 60)
    print("setweight — boost title matches over body matches")
    print("=" * 60)

    with db.cursor() as cur:
        print("  Unweighted search for 'search':\n")
        db.print_table(
            cur,
            """
            SELECT id,
                   title,
                   round(ts_rank(
                       to_tsvector('english', title || ' ' || body),
                       plainto_tsquery('english', 'search')
                   )::numeric, 6) AS rank
            FROM   articles
            WHERE  to_tsvector('english', title || ' ' || body)
                   @@ plainto_tsquery('english', 'search')
            ORDER  BY rank DESC
            """,
            ["id", "title", "rank"],
            truncate=50,
        )

        print("  Weighted search (title=A, body=B) for 'search':\n")
        db.print_table(
            cur,
            """
            SELECT id,
                   title,
                   round(ts_rank(
                       setweight(to_tsvector('english', title), 'A') ||
                       setweight(to_tsvector('english', body),  'B'),
                       plainto_tsquery('english', 'search')
                   )::numeric, 6) AS rank
            FROM   articles
            WHERE  to_tsvector('english', title || ' ' || body)
                   @@ plainto_tsquery('english', 'search')
            ORDER  BY rank DESC
            """,
            ["id", "title", "rank"],
            truncate=50,
        )

    print(
        "  With weighting, articles that mention 'search' in their title\n"
        "  rank above those that only mention it in the body.\n"
        "  setweight(vec, 'A') labels every lexeme in vec as weight A.\n"
        "  || concatenates two tsvectors into one for ranking.\n"
    )


def demo_ts_rank_cd() -> None:
    print("=" * 60)
    print("ts_rank_cd — cover density (term proximity)")
    print("=" * 60)

    with db.cursor() as cur:
        print("  Comparing ts_rank vs ts_rank_cd for 'full text search':\n")
        db.print_table(
            cur,
            """
            SELECT id,
                   title,
                   round(ts_rank(
                       to_tsvector('english', title || ' ' || body),
                       plainto_tsquery('english', 'full text search')
                   )::numeric, 6) AS rank,
                   round(ts_rank_cd(
                       to_tsvector('english', title || ' ' || body),
                       plainto_tsquery('english', 'full text search')
                   )::numeric, 6) AS rank_cd
            FROM   articles
            WHERE  to_tsvector('english', title || ' ' || body)
                   @@ plainto_tsquery('english', 'full text search')
            ORDER  BY rank_cd DESC
            """,
            ["id", "title", "rank", "rank_cd"],
            truncate=45,
        )

    print(
        "  ts_rank_cd gives higher scores when query terms appear close\n"
        "  together. Articles about FTS where all three terms cluster\n"
        "  in the same sentence rank higher than those where they're spread out.\n"
    )


def demo_ts_headline() -> None:
    print("=" * 60)
    print("ts_headline — extract a highlighted snippet")
    print("=" * 60)

    with db.cursor() as cur:
        print("  Search: 'database index' — headline from body\n")
        cur.execute(
            """
            SELECT title,
                   ts_headline(
                       'english',
                       body,
                       plainto_tsquery('english', 'database index'),
                       'MaxWords=20, MinWords=10, StartSel=>>>, StopSel=<<<'
                   ) AS snippet
            FROM   articles
            WHERE  to_tsvector('english', title || ' ' || body)
                   @@ plainto_tsquery('english', 'database index')
            ORDER  BY ts_rank(
                       to_tsvector('english', title || ' ' || body),
                       plainto_tsquery('english', 'database index')
                   ) DESC
            LIMIT  4
            """
        )
        rows = cur.fetchall()
        for title, snippet in rows:
            print(f"  {title}")
            print(f"  Snippet: {snippet}\n")

    print(
        "  >>> and <<< mark the highlighted terms in the snippet.\n"
        "  In a web app you'd use the default <b>...</b> tags instead.\n"
        "  ts_headline operates on the raw text, not tsvector, so it can\n"
        "  show the original word form ('databases' not 'databas').\n"
    )


def main() -> None:
    demo_ts_rank()
    demo_setweight()
    demo_ts_rank_cd()
    demo_ts_headline()


if __name__ == "__main__":
    main()
