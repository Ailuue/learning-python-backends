# Caching

## What is this?

Reading from a database is slow — typically 1–10 milliseconds per query. That sounds fast, but if your homepage makes 20 queries to render, and 10,000 users are loading it per second, your database is doing 200,000 queries a second. It will collapse.

**Caching** stores the result of an expensive operation somewhere fast (usually memory) so you can reuse it without doing the work again. The next time someone asks for the same data, you return the cached copy in microseconds instead of querying the database.

**Redis** is the most common cache. It's an in-memory key-value store that can serve hundreds of thousands of requests per second and supports expiry times so stale data automatically clears itself.

## The core trade-off

Caching trades **memory** for **speed**, and trades **freshness** for **performance**. Cached data can be stale — if the database changes and the cache doesn't know, users might see old data until the cache expires.

Good caching strategy is mostly about deciding:
1. What to cache (frequently read, rarely changed data)
2. How long to keep it (TTL — time to live)
3. When to invalidate it (when the underlying data changes)

## What the files cover

| File | What it teaches |
|---|---|
| `01_cache_aside.py` | The most common pattern: check cache first, fall back to DB on a miss, write back to cache |
| `02_write_through.py` | Write to the cache and the DB simultaneously — cache is always warm, never stale |
| `03_write_behind.py` | Write to the cache immediately, sync to DB in the background — fastest writes, risk of data loss |
| `04_invalidation.py` | How to clear cached data when the source changes — harder than it sounds |
| `05_stampede.py` | The "thundering herd" problem: when the cache expires and 10,000 requests all hit the DB at once |

## How to run

```bash
# Requires Redis
docker run -p 6379:6379 redis

pip install -r requirements.txt   # (if present, else: pip install redis sqlalchemy psycopg2-binary)

python 01_cache_aside.py
python 02_write_through.py
# ... and so on
```
