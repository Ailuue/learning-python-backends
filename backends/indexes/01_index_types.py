"""
PostgreSQL Index Types
======================
An index is a separate data structure maintained alongside a table. When
PostgreSQL executes a query it can consult the index instead of scanning
every row — but only if the index type supports the operator being used.

The four core index types:

  B-tree  — default, sorted balanced tree.
            Supports: =, <, >, <=, >=, BETWEEN, IN, IS NULL, ORDER BY,
                      LIKE 'prefix%'
            Use for: almost everything — scalar columns you filter, sort,
                     or join on.

  Hash    — hash table, equality only.
            Supports: = only (no ranges, no sorting)
            Use for: columns where you exclusively do exact-match lookups
                     and never range queries. Rarely faster than B-tree in
                     practice; B-tree is almost always good enough.

  GIN     — Generalized Inverted Index. Maps each *element inside* a
            composite value to the rows containing it (like a book index).
            Supports: @> (contains), <@ (contained by), && (overlap),
                      @@ (full-text match), ? (JSON key exists)
            Use for: JSONB, arrays, full-text search (tsvector).
                     Slower to write, very fast to query.

  GiST    — Generalized Search Tree. A framework for spatial/range
            index strategies.
            Supports: && (overlap), @> (contains), <@ (contained by),
                      -|- (adjacent), <-> (distance / KNN)
            Use for: range types (daterange, tsrange), geometric types,
                     full-text search on write-heavy tables.

Demonstration tables used below:
  users     — B-tree on email (equality + ordering)
  sessions  — Hash on token (equality only)
  articles  — GIN on tags array and full-text tsvector
  events    — GiST on a daterange period column
"""

import db


SETUP = """
DROP TABLE IF EXISTS idx_events;
DROP TABLE IF EXISTS idx_articles;
DROP TABLE IF EXISTS idx_sessions;
DROP TABLE IF EXISTS idx_users;

CREATE TABLE idx_users (
    user_id   SERIAL PRIMARY KEY,
    email     TEXT   NOT NULL UNIQUE,
    username  TEXT   NOT NULL
);

CREATE TABLE idx_sessions (
    session_id SERIAL      PRIMARY KEY,
    user_id    INT         NOT NULL REFERENCES idx_users,
    token      TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE idx_articles (
    article_id SERIAL  PRIMARY KEY,
    title      TEXT    NOT NULL,
    body       TEXT    NOT NULL,
    tags       TEXT[]  NOT NULL DEFAULT '{}'
);

CREATE TABLE idx_events (
    event_id SERIAL    PRIMARY KEY,
    name     TEXT      NOT NULL,
    period   DATERANGE NOT NULL
);
"""

CREATE_INDEXES = """
-- B-tree: default index type, supports equality AND range AND ORDER BY.
-- PostgreSQL already created one for the UNIQUE constraint on email,
-- but we add an explicit one on username to show the syntax clearly.
CREATE INDEX idx_btree_username ON idx_users USING BTREE (username);

-- Hash: equality-only. Useful for long tokens where you never do range
-- queries. Notice the USING HASH clause.
CREATE INDEX idx_hash_token ON idx_sessions USING HASH (token);

-- GIN on an array column: accelerates @> (contains) and && (overlap).
CREATE INDEX idx_gin_tags ON idx_articles USING GIN (tags);

-- GIN on a computed tsvector: accelerates @@ (full-text match).
-- to_tsvector normalises words into lexemes ('running' -> 'run').
CREATE INDEX idx_gin_fts ON idx_articles
    USING GIN (to_tsvector('english', title || ' ' || body));

-- GiST on a daterange: accelerates && (overlap) and @> (contains date).
CREATE INDEX idx_gist_period ON idx_events USING GIST (period);
"""

SEED = """
INSERT INTO idx_users (email, username) VALUES
    ('alice@example.com', 'alice'),
    ('bob@example.com',   'bob'),
    ('carol@example.com', 'carol');

INSERT INTO idx_sessions (user_id, token) VALUES
    (1, 'tok_a1b2c3d4e5f6'),
    (2, 'tok_x9y8z7w6v5u4'),
    (3, 'tok_p1q2r3s4t5u6');

INSERT INTO idx_articles (title, body, tags) VALUES
    ('Intro to PostgreSQL',
     'PostgreSQL is a powerful open-source relational database.',
     ARRAY['postgresql', 'database', 'sql']),
    ('Python and Databases',
     'Connecting Python to PostgreSQL using psycopg2 is straightforward.',
     ARRAY['python', 'postgresql', 'psycopg2']),
    ('Full-Text Search in Postgres',
     'GIN indexes accelerate tsvector queries for full-text search.',
     ARRAY['postgresql', 'search', 'gin']),
    ('Getting Started with Redis',
     'Redis is an in-memory key-value store often used for caching.',
     ARRAY['redis', 'caching', 'nosql']);

INSERT INTO idx_events (name, period) VALUES
    ('Python Conference',  '[2026-06-01, 2026-06-03]'),
    ('Database Summit',    '[2026-06-10, 2026-06-12]'),
    ('Cloud Expo',         '[2026-07-05, 2026-07-07]'),
    ('DevOps Days',        '[2026-06-20, 2026-06-21]'),
    ('Security Workshop',  '[2026-05-28, 2026-05-29]');
"""


def demo_btree(cur):
    print("=" * 60)
    print("B-TREE INDEX  (idx_users.email, idx_users.username)")
    print("=" * 60)
    print("Supports equality, range queries, and ORDER BY.\n")

    print("1. Equality lookup — WHERE email = '...'")
    db.print_table(
        cur,
        "SELECT user_id, email, username FROM idx_users WHERE email = %s",
        ["user_id", "email", "username"],
        params=("alice@example.com",),
    )

    print("2. Range + ORDER BY — WHERE username >= 'b' ORDER BY username")
    db.print_table(
        cur,
        """
        SELECT user_id, email, username
        FROM   idx_users
        WHERE  username >= 'b'
        ORDER  BY username
        """,
        ["user_id", "email", "username"],
    )


def demo_hash(cur):
    print("=" * 60)
    print("HASH INDEX  (idx_sessions.token)")
    print("=" * 60)
    print("Supports ONLY equality. No ranges, no sorting.\n")

    print("Exact token lookup — WHERE token = '...'")
    db.print_table(
        cur,
        """
        SELECT s.session_id, u.username, s.token
        FROM   idx_sessions s
        JOIN   idx_users    u ON u.user_id = s.user_id
        WHERE  s.token = %s
        """,
        ["session_id", "username", "token"],
        params=("tok_x9y8z7w6v5u4",),
    )

    print("NOTE: a range query like WHERE token > 'tok_a...' cannot use")
    print("      a Hash index — PostgreSQL would fall back to a seq scan.\n")


def demo_gin_array(cur):
    print("=" * 60)
    print("GIN INDEX  (idx_articles.tags  — array)")
    print("=" * 60)
    print("Supports @> (contains), <@ (contained by), && (overlap).\n")

    print("1. @>  Contains — articles that have BOTH 'postgresql' AND 'python'")
    db.print_table(
        cur,
        """
        SELECT article_id, title, tags
        FROM   idx_articles
        WHERE  tags @> ARRAY['postgresql', 'python']
        """,
        ["article_id", "title", "tags"],
    )

    print("2. &&  Overlap — articles that have ANY of: 'python', 'nosql'")
    db.print_table(
        cur,
        """
        SELECT article_id, title, tags
        FROM   idx_articles
        WHERE  tags && ARRAY['python', 'nosql']
        """,
        ["article_id", "title", "tags"],
    )


def demo_gin_fts(cur):
    print("=" * 60)
    print("GIN INDEX  (to_tsvector(title || body)  — full-text search)")
    print("=" * 60)
    print("@@ matches a tsvector against a tsquery (stemmed word search).\n")

    print("1. Search for 'postgresql' (matches stemmed lexeme 'postgresql')")
    db.print_table(
        cur,
        """
        SELECT article_id, title
        FROM   idx_articles
        WHERE  to_tsvector('english', title || ' ' || body)
                   @@ to_tsquery('english', 'postgresql')
        """,
        ["article_id", "title"],
    )

    print("2. Search for 'index' (stemmer: 'indexes' -> 'index')")
    db.print_table(
        cur,
        """
        SELECT article_id, title
        FROM   idx_articles
        WHERE  to_tsvector('english', title || ' ' || body)
                   @@ to_tsquery('english', 'index')
        """,
        ["article_id", "title"],
    )

    print("3. Phrase search using & (AND) — must contain 'full' AND 'text'")
    db.print_table(
        cur,
        """
        SELECT article_id, title
        FROM   idx_articles
        WHERE  to_tsvector('english', title || ' ' || body)
                   @@ to_tsquery('english', 'full & text')
        """,
        ["article_id", "title"],
    )


def demo_gist(cur):
    print("=" * 60)
    print("GiST INDEX  (idx_events.period  — daterange)")
    print("=" * 60)
    print("Supports && (overlap), @> (contains), <@ (contained by).\n")

    print("1. && Overlap — events that overlap June 2026")
    db.print_table(
        cur,
        """
        SELECT event_id, name, period
        FROM   idx_events
        WHERE  period && '[2026-06-01, 2026-06-30]'::daterange
        ORDER  BY lower(period)
        """,
        ["event_id", "name", "period"],
    )

    print("2. @> Contains date — events running on June 10")
    db.print_table(
        cur,
        """
        SELECT event_id, name, period
        FROM   idx_events
        WHERE  period @> '2026-06-10'::date
        """,
        ["event_id", "name", "period"],
    )


def show_indexes(cur):
    print("=" * 60)
    print("ALL INDEXES ON OUR TABLES")
    print("=" * 60)
    db.print_table(
        cur,
        """
        SELECT
            indexname,
            tablename,
            indexdef
        FROM   pg_indexes
        WHERE  tablename LIKE 'idx_%'
        ORDER  BY tablename, indexname
        """,
        ["index_name", "table", "definition"],
    )


def main():
    with db.cursor() as cur:
        cur.execute(SETUP)
        cur.execute(CREATE_INDEXES)
        cur.execute(SEED)

        show_indexes(cur)
        demo_btree(cur)
        demo_hash(cur)
        demo_gin_array(cur)
        demo_gin_fts(cur)
        demo_gist(cur)

        print("=" * 60)
        print("SUMMARY: which index to reach for")
        print("=" * 60)
        print("  B-tree  — your default. Scalars, equality, ranges, ORDER BY.")
        print("  Hash    — equality-only columns (tokens, UUIDs). Rarely needed.")
        print("  GIN     — JSONB, arrays, full-text search. Read-heavy data.")
        print("  GiST    — ranges (daterange), geometry, write-heavy FTS.")
        print()
        print("When in doubt: create a B-tree and use EXPLAIN ANALYZE to")
        print("see whether a different type would help.")


if __name__ == "__main__":
    main()
