# Bookmark Manager

Full-featured FastAPI backend for saving, organizing, and tagging bookmarks.

## Features

- JWT authentication (register, login, refresh tokens)
- CRUD for bookmarks, categories, and tags
- Redis-backed rate limiting via SlowAPI
- Celery background tasks
- Alembic database migrations
- Dockerized dev and test environments

## Stack

| Layer | Tool |
|---|---|
| API | FastAPI |
| Database | PostgreSQL + SQLAlchemy |
| Migrations | Alembic |
| Cache / rate limiting | Redis + SlowAPI |
| Background tasks | Celery |
| Auth | JWT (python-jose) |

## Structure

```
app/
  main.py           — app factory, middleware, lifespan hooks
  config.py         — settings via pydantic-settings
  database.py       — engine and session factory
  security.py       — password hashing and JWT helpers
  rate_limit.py     — SlowAPI limiter setup
  models/           — SQLAlchemy ORM models (bookmark, category, tag, user)
  routers/          — auth, bookmarks, categories, tags
  schemas/          — Pydantic request and response models
tests/              — pytest test suite
alembic/            — migration scripts
```

## Setup

```bash
# Start Postgres and Redis
docker compose up -d

# Apply migrations
docker compose exec app alembic upgrade head

# Run tests
docker compose -f docker-compose.test.yml up --build
```

API docs are at http://localhost:8000/docs once the app is running.
