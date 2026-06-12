# Database Migration Demo

Hands-on Alembic practice: write migrations, apply them, roll them back, and migrate existing data.

## Domain

A small library database — `Author` and `Book` tables — that evolves through a series of schema changes.

## What you'll learn

- How to create and autogenerate Alembic migration scripts
- `alembic upgrade head` / `alembic downgrade -1`
- Adding a column, changing a column type, and dropping a column
- Data migrations: transforming existing rows as part of a schema change
- Reading migration history with `alembic history` and `alembic current`

## Files

| File | Purpose |
|---|---|
| `models.py` | SQLAlchemy ORM models (the current schema) |
| `database.py` | Engine and session setup |
| `seed.py` | Populate the database with sample data |
| `migrate_data.py` | Script that runs a data migration step |
| `alembic/` | Auto-generated and hand-written migration scripts |

## Setup

```bash
pip install -r requirements.txt

# Bring the schema up to the latest version
alembic upgrade head

# Seed with sample data
python seed.py
```

## Common Alembic commands

```bash
alembic revision --autogenerate -m "add email to authors"  # generate from model diff
alembic upgrade head        # apply all pending migrations
alembic downgrade -1        # roll back one migration
alembic history             # list all revisions
alembic current             # show which revision the database is on
```
