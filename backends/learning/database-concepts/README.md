# Database Concepts

PostgreSQL and SQLAlchemy patterns, each in a self-contained runnable folder.

## Modules

| Folder | What it covers |
|---|---|
| [async_sqlalchemy/](async_sqlalchemy/) | Async SQLAlchemy sessions, `asyncpg` driver, `async with` session patterns |
| [db-migration-demo/](db-migration-demo/) | Alembic schema migrations: create, alter, seed, roll back |
| [full_text_search/](full_text_search/) | PostgreSQL `tsvector` / `tsquery` full-text search with ranking |
| [indexes/](indexes/) | B-tree, partial, composite, and expression indexes — when and why |
| [n_plus_one/](n_plus_one/) | The N+1 query problem and how `joinedload` / `selectinload` fix it |
| [normalization/](normalization/) | 1NF → 3NF normalization with practical schema examples |
| [pgvector-demo/](pgvector-demo/) | Vector similarity search with `pgvector` and local Ollama embeddings |
| [transactions/](transactions/) | ACID transactions, savepoints, isolation levels, and rollback patterns |
| [window_functions/](window_functions/) | `ROW_NUMBER`, `RANK`, `LAG`, `LEAD`, running totals, and moving averages |
