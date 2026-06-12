# pgvector Demo

Store and search text using vector embeddings in PostgreSQL via the `pgvector` extension.

## What it does

1. Seeds the database with users and their comments
2. Embeds each comment using a local Ollama model (768-dimensional vectors)
3. Finds semantically similar comments using cosine distance — no keyword matching needed

## Why vectors?

A keyword search for "fast car" misses "quick vehicle" or "speedy automobile". Embeddings encode meaning, so semantically similar text ends up close in vector space regardless of the exact words used.

## Stack

| Tool | Role |
|---|---|
| PostgreSQL + pgvector | Stores vectors and runs similarity queries |
| SQLAlchemy | ORM with `pgvector.sqlalchemy.Vector` column type |
| Ollama | Local embedding model server |
| `nomic-embed-text` | Default embedding model (768 dimensions) |

## Setup

```bash
# 1. Install and start Ollama, then pull the model
ollama pull nomic-embed-text

# 2. Start PostgreSQL with pgvector
docker compose up -d

# 3. Apply migrations and seed data
pip install -r requirements.txt
alembic upgrade head
python seed.py

# 4. Generate embeddings for all comments
python embed_comments.py
```

## Running a similarity search

After embedding, open a Python shell or add queries to `embed_comments.py`:

```python
# Find the 5 comments most similar to a query string
query_vec = ollama.embed("nomic-embed-text", "something hilarious")
results = session.execute(
    select(Comment).order_by(Comment.embedding.cosine_distance(query_vec)).limit(5)
)
```

## Switching models

```bash
python embed_comments.py --model mxbai-embed-large
```

Note: switching models changes the vector dimensions — you'll need to re-run the migration to update the column size and re-embed all rows.
