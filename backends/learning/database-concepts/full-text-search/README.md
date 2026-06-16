# Full-Text Search

## What is this?

A regular database query can find exact matches: `WHERE name = 'Alice'`. But what about searching a library of blog posts for articles about "database performance tips"? You need something that understands language — that "tips" might appear as "tip" or "tips", that "database" and "databases" are the same word, and that results should be ranked by relevance.

**Full-text search** is a database feature that indexes the content of text columns for language-aware searching. PostgreSQL has this built in, and it's often good enough that you don't need a separate search engine like Elasticsearch.

## How it works

PostgreSQL converts text into a **tsvector** — a sorted list of normalized word roots (called lexemes) with position information. "Running fast" becomes `'fast':2 'run':1`. Your search query becomes a **tsquery** — a logical expression of terms.

Searching is then a set operation: does this document's tsvector contain the terms in the tsquery?

```sql
-- Find all posts containing words related to "database" AND "index"
SELECT title FROM posts
WHERE to_tsvector('english', body) @@ to_tsquery('english', 'database & index');
```

The `'english'` language parameter tells PostgreSQL to use English stemming rules — so "running" matches "run", "indexes" matches "index", etc.

## When to use PostgreSQL FTS vs. Elasticsearch

PostgreSQL full-text search is a great fit when:
- Your data is already in PostgreSQL
- Search is one feature among many, not the core product
- You want simplicity over maximum relevance tuning

Reach for Elasticsearch or similar when:
- Search is the core of your product
- You need complex relevance scoring, synonyms, or fuzzy matching
- You're searching billions of documents

## What the files cover

| File | What it teaches |
|---|---|
| `01_basics.py` | Creating tsvectors and tsqueries; the `@@` match operator; multi-column search |
| `02_ranking.py` | `ts_rank` — scoring results by relevance so the best matches come first |
| `03_indexes.py` | GIN indexes — how to make FTS queries fast even on large tables |

## How to run

```bash
# Start the shared Postgres for all database-concepts modules (first run creates
# this module's database automatically). Skip if it's already running.
(cd .. && docker compose up -d)

pip install -r requirements.txt

python 01_basics.py
python 02_ranking.py
python 03_indexes.py
```
