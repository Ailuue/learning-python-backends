# Database Concepts

> 📚 [Backend Learning](../README.md) · **Core path · step 3 of 4** · [⬅ testing-concepts](../testing-concepts/) · Next: [backend-concepts ➡](../backend-concepts/)

PostgreSQL and SQLAlchemy patterns, each in a self-contained runnable folder.

## Quick start — one Postgres for the whole folder

Every module here talks to Postgres on `localhost:5432` as `postgres` / `postgres`.
A single shared compose file provisions a database for each module on first start,
so you set up the database layer **once**:

```bash
# from this directory (backends/learning/database-concepts/)
docker compose up -d        # starts Postgres + creates every module's database
```

That's it — the connection defaults baked into each module's `db.py` already match,
so you don't need a `.env` file. Then run any module:

```bash
cd n-plus-one
pip install -r requirements.txt
python 01_n_plus_one.py
```

The container uses the `pgvector` image, so the [pgvector-demo/](pgvector-demo/) module
works against the same Postgres with the `vector` extension already enabled.

When you're done: `docker compose down` (keep data) or `docker compose down -v` (wipe).

> `db-migration-demo/` starts from a local SQLite file and only needs Postgres for the
> optional `migrate_data.py` step; everything else uses the shared container above.

## Modules

| Folder | What it covers |
|---|---|
| [async-sqlalchemy/](async-sqlalchemy/) | Async SQLAlchemy sessions, `asyncpg` driver, `async with` session patterns |
| [db-migration-demo/](db-migration-demo/) | Alembic schema migrations: create, alter, seed, roll back |
| [full-text-search/](full-text-search/) | PostgreSQL `tsvector` / `tsquery` full-text search with ranking |
| [indexes/](indexes/) | B-tree, partial, composite, and expression indexes — when and why |
| [n-plus-one/](n-plus-one/) | The N+1 query problem and how `joinedload` / `selectinload` fix it |
| [normalization/](normalization/) | 1NF → 3NF normalization with practical schema examples |
| [pgvector-demo/](pgvector-demo/) | Vector similarity search with `pgvector` and local Ollama embeddings |
| [transactions/](transactions/) | ACID transactions, savepoints, isolation levels, and rollback patterns |
| [window-functions/](window-functions/) | `ROW_NUMBER`, `RANK`, `LAG`, `LEAD`, running totals, and moving averages |
