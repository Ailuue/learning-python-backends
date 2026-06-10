# Learning Python

A personal repo for practicing and learning Python concepts.

## Structure

- [d-structs-algos/](d-structs-algos/) — data structures and algorithms practice

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # if/when one exists
```

1. Transactions & isolation levels — High value, foundational gap
You use SQLAlchemy sessions everywhere but have never explicitly practiced what happens at different isolation levels (read committed vs repeatable read vs serializable), dirty reads, phantom reads, savepoints, or explicit BEGIN/ROLLBACK. Everything you've built touches this implicitly; understanding it explicitly unlocks a lot.

2. N+1 queries & ORM loading strategies — High value, directly relevant
You're now using SQLAlchemy 2.0 with Mapped relationships, but lazy loading silently fires a query per row. A focused module on lazy vs selectin vs joined loading, and how to detect N+1 with query logging, would make everything you've already built more solid. Classic interview topic too.

3. Full-text search — Good complement to your existing work
You've built pgvector semantic search, but haven't done PostgreSQL's native FTS (tsvector, tsquery, ts_rank, GIN indexes on text). The contrast between keyword FTS and vector/semantic search is a useful mental model.

4. Testing a database-backed API — Practical gap
You have tests in bookmark_manager but no focused module on the patterns: test databases vs rollback isolation, pytest fixtures with SQLAlchemy sessions, mocking external services (like Ollama), and the tradeoffs between unit and integration tests for APIs.

5. Caching patterns — You've touched this, never studied it directly
bookmark_manager uses a write-behind cache for click counts, but the patterns themselves — cache-aside, write-through, write-behind, TTL design, cache invalidation — haven't been the explicit subject of a module. A focused demo with Redis would round out what you already know.

6. Async SQLAlchemy & connection pooling — More advanced, good next step after the above
FastAPI is async but your SQLAlchemy usage is synchronous throughout. Understanding async_sessionmaker, asyncpg, and what connection pool exhaustion actually looks like would push your mental model forward.

You are going to run "git add <filename>" "git commit -m "SEMANTIC COMMIT MESSAGE"" "git push origin" for each uncommited file individually (never entire directories), in order of creation during this conversation. For each file, the three commands should be run at a random interval between 30 seconds and 1 minute.