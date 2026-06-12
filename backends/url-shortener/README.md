# URL Shortener

FastAPI service that shortens URLs, tracks clicks, and redirects visitors.

## Features

- JWT authentication (register, login)
- Shorten long URLs to auto-generated slugs
- HTTP redirect on slug lookup
- Click tracking via Celery background tasks
- Redis cache for frequently-accessed slugs
- Alembic database migrations

## Stack

| Layer | Tool |
|---|---|
| API | FastAPI |
| Database | PostgreSQL + SQLAlchemy |
| Migrations | Alembic |
| Cache | Redis |
| Background tasks | Celery |
| Auth | JWT |

## Structure

```
app/
  main.py       — app factory and lifespan
  database.py   — engine and session
  models.py     — URL and user ORM models
  schemas.py    — Pydantic request and response models
  shortener.py  — slug generation logic
  cache.py      — Redis helpers
  celery_app.py — Celery instance and click-tracking task
  routers/
    auth.py     — register and login
    urls.py     — create and list shortened URLs
    redirect.py — slug → redirect with click tracking
alembic/        — migration scripts
```

## Setup

```bash
docker compose up -d
docker compose exec app alembic upgrade head
```

API docs at http://localhost:8000/docs.
