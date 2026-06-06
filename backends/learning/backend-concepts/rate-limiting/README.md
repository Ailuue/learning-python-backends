# Rate Limiting

## What is this?

Imagine your API is a coffee shop with one barista. If one customer orders 500 coffees at once, everyone else has to wait. **Rate limiting** is the sign on the door that says "maximum 5 orders per minute per customer."

Every public API uses rate limiting. Without it, a single buggy script, an angry user, or a malicious bot can send millions of requests and bring your server to its knees. With it, each client gets a fair share of your capacity, and abusers are automatically throttled before they cause damage.

Rate limiting also protects downstream systems — your database, payment provider, or email service — that have their own limits you'd rather not hit.

## The three main algorithms

**Fixed window** — divide time into buckets (e.g., one per minute). Count requests per bucket. Simple, but a client can burst 2× the limit across a bucket boundary.

**Sliding window** — instead of fixed buckets, look at the last N seconds from right now. More accurate, slightly more memory.

**Token bucket** — a bucket fills with tokens at a fixed rate. Each request spends a token. Empty bucket = denied. This allows short bursts while enforcing a long-term average rate. Closest to how humans naturally behave.

## When would you use this?

- Any public or semi-public API
- Login endpoints (prevent password brute-forcing)
- Expensive endpoints like search or file upload
- Anywhere you pay per downstream API call

## What the files cover

| File | What it teaches |
|---|---|
| `01_fixed_window.py` | Simplest algorithm; includes a demo that shows the boundary burst flaw |
| `02_sliding_window.py` | Fixes the boundary problem using a Redis sorted set |
| `03_token_bucket.py` | Allows bursting; uses a Lua script for atomic read-modify-write |
| `04_middleware.py` | Wraps sliding window into FastAPI middleware; different limits per route |
| `redis_rl.py` | Shared Redis client used by all scripts |

## How to run

```bash
# Requires Redis
docker run -p 6379:6379 redis

pip install -r requirements.txt

# Standalone demos (no server needed):
python 01_fixed_window.py
python 02_sliding_window.py
python 03_token_bucket.py

# FastAPI middleware demo:
uvicorn 04_middleware:app --reload
curl -i http://localhost:8000/
curl -i http://localhost:8000/search   # stricter limit — hit it several times quickly
```
