# Async SQLAlchemy

## What is this?

Python code normally runs one line at a time. When a line talks to a database, Python stops and waits for the database to reply before moving on. For a server handling thousands of requests, this waiting time is wasted — the CPU is sitting idle while the database does its work.

**Async programming** solves this by letting Python do other work while it waits. Instead of blocking, Python says "I'm waiting for the database — let me handle another request in the meantime." When the database responds, Python comes back and picks up where it left off.

**SQLAlchemy** is the most popular Python library for talking to databases. Its async version (`AsyncSession`, `asyncpg`) is built on top of Python's `asyncio` system and works natively with async web frameworks like FastAPI.

## The key difference

```python
# Sync — blocks the entire thread while waiting
user = session.get(User, user_id)

# Async — suspends this coroutine, frees the thread for other work
user = await session.get(User, user_id)
```

The `await` keyword is the signal that says "pause here, do other work, come back when the result is ready."

## When does it matter?

Async shines when your app is **I/O bound** — spending most of its time waiting for databases, APIs, or file reads rather than crunching numbers. A FastAPI server handling 1,000 concurrent users fetching data from a database will perform significantly better with async than sync.

It doesn't help (and adds complexity) for CPU-heavy work like image processing or data analysis.

## What the files cover

| File | What it teaches |
|---|---|
| `01_async_basics.py` | Creating an async session and running your first `await` query |
| `02_async_sessionmaker.py` | The right way to create sessions in a real app — factories and dependency injection |
| `03_connection_pool.py` | How connection pools work: a limited number of database connections shared between many requests |
| `04_pool_exhaustion.py` | What happens when all connections are busy — timeouts, errors, and how to tune pool size |
| `05_concurrent_queries.py` | Running multiple database queries at the same time with `asyncio.gather` |

## How to run

```bash
# Requires PostgreSQL
docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres

pip install -r requirements.txt   # (if present, else: pip install sqlalchemy asyncpg)

python 01_async_basics.py
python 02_async_sessionmaker.py
# ... and so on
```
