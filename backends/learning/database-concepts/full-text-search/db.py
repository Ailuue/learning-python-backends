import os
import textwrap
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "full_text_search_demo"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


@contextmanager
def cursor():
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()


def one(cur) -> tuple:
    """
    The next row, or an error if the query returned none.

    psycopg2 types fetchone() as Optional because a SELECT can match nothing.
    Queries that must return a row (aggregates, RETURNING clauses, lookups by
    primary key) should say so rather than let None reach the caller and fail
    later as a confusing "NoneType is not subscriptable".
    """
    row = cur.fetchone()
    if row is None:
        raise LookupError(f"expected a row, got none: {cur.query!r}")
    return row


def scalar(cur):
    """First column of the next row. See one()."""
    return one(cur)[0]


def print_table(cur, query: str, headers: list[str], params=None, truncate: int = 60) -> None:
    cur.execute(query, params)
    rows = cur.fetchall()
    if not rows:
        print("  (no rows)\n")
        return
    str_rows = [
        tuple(textwrap.shorten(str(v), truncate, placeholder="…") if v is not None else "NULL"
              for v in row)
        for row in rows
    ]
    widths = [
        max(len(h), max(len(r[i]) for r in str_rows))
        for i, h in enumerate(headers)
    ]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("  ".join("-" * w for w in widths))
    for row in str_rows:
        print(fmt.format(*row))
    print()


SETUP = """
DROP TABLE IF EXISTS articles;

CREATE TABLE articles (
    id           SERIAL PRIMARY KEY,
    title        TEXT NOT NULL,
    body         TEXT NOT NULL,
    author       TEXT NOT NULL
);
"""

SEED = """
INSERT INTO articles (title, body, author) VALUES

('Introduction to PostgreSQL Indexes',
 'Indexes are data structures that speed up data retrieval in PostgreSQL. '
 'A B-tree index is the default and works well for equality and range queries. '
 'Without an index, PostgreSQL performs a sequential scan of every row in the table. '
 'Choosing the right index type dramatically improves database query performance.',
 'alice'),

('Full-Text Search in PostgreSQL',
 'PostgreSQL provides powerful full-text search capabilities using tsvector and tsquery. '
 'A tsvector is a sorted list of lexemes — normalised word forms stripped of suffixes. '
 'The @@ operator tests whether a tsquery matches a tsvector. '
 'Full-text search is far more flexible than LIKE because it understands language.',
 'bob'),

('Python and Database Performance',
 'Python applications often become slow because of inefficient database queries. '
 'Using an ORM like SQLAlchemy can hide N+1 query problems from the developer. '
 'Profiling database queries from Python requires hooking into the connection layer. '
 'Caching query results in Redis can dramatically reduce database load.',
 'alice'),

('Understanding Database Transactions',
 'A transaction is a unit of work that either completes fully or not at all. '
 'PostgreSQL supports four isolation levels: read committed, repeatable read, and serializable. '
 'Write skew is a subtle anomaly that only the serializable isolation level prevents. '
 'Every application that modifies data should understand transaction boundaries.',
 'carol'),

('Indexing Strategies for Web Applications',
 'Web applications need indexes on columns used in WHERE clauses and JOIN conditions. '
 'Partial indexes reduce index size by covering only the rows that match a condition. '
 'A composite index on (user_id, created_at) can serve both filtering and sorting. '
 'Over-indexing slows down writes because every index must be updated on INSERT.',
 'bob'),

('Python ORM vs Raw SQL',
 'SQLAlchemy and Django ORM generate SQL automatically from Python model definitions. '
 'Raw SQL gives full control but requires careful parameterisation to avoid injection. '
 'ORMs excel at managing relationships and migrations but can generate inefficient queries. '
 'The best Python database code uses an ORM for structure and raw SQL for performance.',
 'alice'),

('Building a Search Engine with PostgreSQL',
 'PostgreSQL full-text search can power a basic search engine without external tools. '
 'Storing a precomputed tsvector column avoids recomputing it on every search query. '
 'Ranking results with ts_rank orders documents by term frequency and proximity. '
 'For semantic search, combine full-text search with pgvector embeddings.',
 'carol'),

('Optimising PostgreSQL Queries',
 'EXPLAIN ANALYZE reveals the actual execution plan and timing of any query. '
 'A sequential scan on a large table is almost always a sign of a missing index. '
 'Vacuuming keeps table statistics fresh so the query planner makes good decisions. '
 'Rewriting a correlated subquery as a JOIN can reduce execution time significantly.',
 'bob'),

('Database Normalisation and Design',
 'Normalisation removes redundancy by splitting data into related tables. '
 'Third normal form ensures that every non-key column depends only on the primary key. '
 'Denormalising for read performance is a deliberate trade-off, not a mistake. '
 'A well-designed schema makes queries simple and indexes effective.',
 'alice'),

('Vector Search and Semantic Similarity',
 'Vector databases store high-dimensional embeddings that represent meaning. '
 'Cosine similarity measures the angle between two vectors in embedding space. '
 'pgvector adds a vector column type and approximate nearest-neighbour search to PostgreSQL. '
 'Semantic search finds results that are conceptually related, not just keyword matches.',
 'carol'),

('PostgreSQL Window Functions',
 'Window functions compute a value for each row using a set of related rows. '
 'Unlike GROUP BY, window functions do not collapse rows — every row is preserved. '
 'ROW_NUMBER, RANK, and DENSE_RANK are the most common ranking window functions. '
 'Running totals and moving averages are easily expressed with OVER and frame clauses.',
 'bob'),

('Caching Strategies for Database Applications',
 'A cache stores frequently read results so the database is queried less often. '
 'Cache-aside loads data on cache miss and writes to the cache after reading. '
 'Write-through keeps the cache and database in sync by writing to both simultaneously. '
 'Redis is the most popular in-memory cache for Python and PostgreSQL applications.',
 'alice'),

('PostgreSQL Full-Text Search vs Elasticsearch',
 'Elasticsearch is a dedicated search engine built on Lucene with horizontal scaling. '
 'PostgreSQL full-text search avoids the complexity of running a separate search service. '
 'For most applications with under a million documents, PostgreSQL search is sufficient. '
 'Elasticsearch offers more advanced ranking models and real-time index updates.',
 'carol'),

('Pagination in REST APIs',
 'Offset pagination is simple but becomes slow as the offset grows larger. '
 'Cursor-based pagination uses the last seen ID to fetch the next page efficiently. '
 'A GIN index on a tsvector column makes full-text search work well with pagination. '
 'Always include a stable sort order when paginating to avoid duplicate or missing rows.',
 'bob'),

('Rate Limiting and API Security',
 'Rate limiting protects an API from abuse by capping requests per client per window. '
 'A token bucket algorithm allows short bursts while enforcing a long-term average. '
 'Storing rate limit counters in Redis gives sub-millisecond read and write performance. '
 'API keys should be hashed before storage so a database breach does not expose them.',
 'alice');
"""
