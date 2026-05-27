"""
Stored tsvector, Triggers, and GIN Indexes
==========================================
The queries in 01 and 02 call to_tsvector() on every row at search time.
With 15 rows that's fine. With 1 million rows, every search scans the
entire table and recomputes every tsvector — slow and CPU-intensive.

The production pattern has three parts:

  1. Stored tsvector column
     Add a search_vector column and populate it once. Searching
     against this column is cheap compared to computing it live.

  2. Trigger to keep it current
     An INSERT or UPDATE to title/body must recompute the vector.
     A BEFORE trigger does this automatically so application code
     never has to think about it.

  3. GIN index on the stored column
     GIN (Generalised Inverted Index) maps each lexeme to the rows
     that contain it — exactly like the index at the back of a book.
     A search finds matching lexemes in the index and jumps directly
     to those rows. No sequential scan required.

GIN vs GiST for tsvector:
  GIN   — faster reads, slower writes/updates. Best for mostly-static
           text (articles, docs). This is the standard choice for FTS.
  GiST  — faster updates, slower reads. Better if the indexed column
           changes frequently. The difference rarely matters at small scale.

EXPLAIN ANALYZE output:
  Seq Scan   — reads every row. Cost grows linearly with table size.
  Bitmap Heap Scan + Bitmap Index Scan on the GIN index
             — looks up matching rows in the index first, then fetches
               only those rows. Cost is proportional to result size,
               not table size.
"""

import db


ADD_COLUMN = """
ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS search_vector TSVECTOR;
"""

POPULATE_COLUMN = """
UPDATE articles
SET search_vector =
    setweight(to_tsvector('english', title), 'A') ||
    setweight(to_tsvector('english', body),  'B');
"""

CREATE_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION articles_search_vector_update()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', NEW.title), 'A') ||
        setweight(to_tsvector('english', NEW.body),  'B');
    RETURN NEW;
END;
$$;
"""

CREATE_TRIGGER = """
DROP TRIGGER IF EXISTS articles_search_vector_trigger ON articles;
CREATE TRIGGER articles_search_vector_trigger
    BEFORE INSERT OR UPDATE OF title, body ON articles
    FOR EACH ROW EXECUTE FUNCTION articles_search_vector_update();
"""

CREATE_GIN_INDEX = """
CREATE INDEX IF NOT EXISTS articles_search_vector_gin
    ON articles USING GIN (search_vector);
"""


def demo_stored_column() -> None:
    print("=" * 60)
    print("STORED TSVECTOR COLUMN — compute once, query many times")
    print("=" * 60)

    with db.cursor() as cur:
        cur.execute(ADD_COLUMN)
        cur.execute(POPULATE_COLUMN)

        print("  search_vector column populated. Sample rows:\n")
        cur.execute(
            "SELECT id, title, search_vector FROM articles ORDER BY id LIMIT 3"
        )
        for id_, title, vec in cur.fetchall():
            print(f"  [{id_}] {title}")
            print(f"       {str(vec)[:120]}…\n")

    print(
        "  The tsvector includes position and weight labels:\n"
        "    'databas':4A  — lexeme 'databas', position 4, weight A (from title)\n"
        "    'index':5B    — lexeme 'index', position 5, weight B (from body)\n"
        "  The A/B weights were set by setweight() when populating.\n"
    )


def demo_trigger() -> None:
    print("=" * 60)
    print("TRIGGER — keep search_vector in sync automatically")
    print("=" * 60)

    with db.cursor() as cur:
        cur.execute(CREATE_TRIGGER_FN)
        cur.execute(CREATE_TRIGGER)

        print("  Inserting a new article WITHOUT setting search_vector:\n")
        cur.execute(
            """
            INSERT INTO articles (title, body, author)
            VALUES ('Trigger Test Article',
                    'This article tests that the trigger fires on insert.',
                    'alice')
            RETURNING id, title, search_vector
            """
        )
        id_, title, vec = cur.fetchone()
        print(f"  id={id_}  title='{title}'")
        print(f"  search_vector set by trigger: {str(vec)[:100]}…\n")

        print("  Updating the title — trigger should recompute:\n")
        cur.execute(
            """
            UPDATE articles
            SET title = 'Updated Trigger Test Article'
            WHERE id = %s
            RETURNING title, search_vector
            """,
            (id_,),
        )
        new_title, new_vec = cur.fetchone()
        print(f"  New title: '{new_title}'")
        print(f"  New vector: {str(new_vec)[:100]}…\n")

        # Clean up test row
        cur.execute("DELETE FROM articles WHERE id = %s", (id_,))

    print(
        "  The trigger fires BEFORE INSERT OR UPDATE OF title, body.\n"
        "  Application code never touches search_vector directly —\n"
        "  it's always derived from title and body automatically.\n"
    )


def demo_gin_index_and_explain() -> None:
    print("=" * 60)
    print("GIN INDEX — EXPLAIN ANALYZE before and after")
    print("=" * 60)

    with db.cursor() as cur:
        query = "plainto_tsquery('english', 'database index')"

        print("  Without GIN index — sequential scan:\n")
        cur.execute(
            f"""
            EXPLAIN ANALYZE
            SELECT id, title
            FROM   articles
            WHERE  to_tsvector('english', title || ' ' || body) @@ {query}
            """
        )
        for (line,) in cur.fetchall():
            print(f"    {line}")
        print()

        cur.execute(CREATE_GIN_INDEX)
        cur.execute("ANALYZE articles")

        print("  With stored search_vector column (no GIN index yet):\n")
        cur.execute(
            f"""
            EXPLAIN ANALYZE
            SELECT id, title
            FROM   articles
            WHERE  search_vector @@ {query}
            """
        )
        for (line,) in cur.fetchall():
            print(f"    {line}")
        print()

        # With only 15 rows the planner correctly prefers a seq scan even with
        # the GIN index present — index overhead outweighs the benefit at this
        # size. SET enable_seqscan = off forces the planner to use the index so
        # we can see what the index plan looks like. In production with large
        # tables the planner uses the GIN index automatically.
        cur.execute("SET enable_seqscan = off")
        print("  With GIN index (enable_seqscan=off to force index plan at small scale):\n")
        cur.execute(
            f"""
            EXPLAIN ANALYZE
            SELECT id, title
            FROM   articles
            WHERE  search_vector @@ {query}
            """
        )
        for (line,) in cur.fetchall():
            print(f"    {line}")
        cur.execute("SET enable_seqscan = on")
        print()

    print(
        "  Three stages of improvement:\n"
        "  Stage 1 — live to_tsvector() per row:\n"
        "    cost=146  — tsvector recomputed for every row on every search.\n"
        "  Stage 2 — stored search_vector column, no index:\n"
        "    cost=3    — stored column read directly, no recomputation.\n"
        "               Still a seq scan, but the per-row work is gone.\n"
        "  Stage 3 — GIN index on search_vector:\n"
        "    Bitmap Index Scan — index maps lexemes → row IDs, then fetches\n"
        "    only matching rows. Cost and time grow with result count,\n"
        "    not table size. With 1 M rows: Stage 1 = seconds, Stage 3 = ms.\n"
    )


def demo_query_with_stored_vector() -> None:
    print("=" * 60)
    print("FINAL PATTERN — stored vector + GIN + weighted ranking")
    print("=" * 60)

    with db.cursor() as cur:
        print("  Search: 'full text search' — production-ready query\n")
        db.print_table(
            cur,
            """
            SELECT id,
                   title,
                   author,
                   round(ts_rank(search_vector,
                       plainto_tsquery('english', 'full text search')
                   )::numeric, 5) AS rank
            FROM   articles
            WHERE  search_vector @@ plainto_tsquery('english', 'full text search')
            ORDER  BY rank DESC
            """,
            ["id", "title", "author", "rank"],
            truncate=48,
        )

    print(
        "  This query:\n"
        "    • Uses the stored search_vector (no recomputation)\n"
        "    • Hits the GIN index (no sequential scan)\n"
        "    • Ranks with A/B weights already embedded in the vector\n"
        "  Adding ts_headline() around body gives you ranked + highlighted\n"
        "  results in a single query — the complete FTS stack.\n"
    )


def main() -> None:
    demo_stored_column()
    demo_trigger()
    demo_gin_index_and_explain()
    demo_query_with_stored_vector()


if __name__ == "__main__":
    main()
