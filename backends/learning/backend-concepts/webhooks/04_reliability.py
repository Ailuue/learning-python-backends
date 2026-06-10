"""
04_reliability.py — Retries, Backoff, and Idempotency

Real webhook delivery needs three things:

1. Retries with exponential backoff
   Receivers go down. Networks blip. A sender must retry failed deliveries,
   waiting longer between each attempt (1s, 2s, 4s, 8s…) so it doesn't
   hammer a struggling service.

2. At-least-once delivery
   Retrying means a receiver might get the same event more than once.
   This is unavoidable — the sender can't know if processing happened
   when the receiver processed successfully but returned 500. Senders
   guarantee delivery, not exactly-once delivery.

3. Idempotency on the receiver
   The receiver must handle duplicates gracefully. Track which event IDs
   have been processed and skip any that arrive again.

This file defines two separate ASGI apps in one module so you can see
both sides. Run them with explicit app targets.

Run:
    uvicorn 04_reliability:receiver_app --port 8001 --reload
    uvicorn 04_reliability:sender_app   --port 8000 --reload

    # Register both endpoints
    curl -X POST "http://localhost:8000/webhooks/register?url=http://localhost:8001/webhook"
    curl -X POST "http://localhost:8000/webhooks/register?url=http://localhost:8001/flaky"

    # Fire an order and watch retry backoff in the sender terminal
    curl -X POST "http://localhost:8000/orders?item=headphones"

    # The flaky endpoint fails twice then succeeds.
    # The /processed count should be 1, not 3 — idempotency at work.
    curl http://localhost:8001/processed
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# ── Sender ─────────────────────────────────────────────────────────────────────

sender_app = FastAPI()

registered_urls: list[str] = []

MAX_ATTEMPTS = 5
BASE_DELAY = 1.0  # seconds; doubles each retry


@sender_app.post("/webhooks/register")
def register_webhook(url: str):
    if url not in registered_urls:
        registered_urls.append(url)
    return {"registered": url}


@sender_app.post("/orders")
async def create_order(item: str):
    order_id = uuid.uuid4().hex[:8]
    event = {
        "id": f"evt_{uuid.uuid4().hex[:12]}",
        "event": "order.created",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"order_id": order_id, "item": item},
    }
    asyncio.create_task(dispatch_with_retry(event, registered_urls[:]))
    return {"order_id": order_id}


async def _try_deliver(client: httpx.AsyncClient, url: str, body: bytes) -> bool:
    try:
        resp = await client.post(
            url,
            content=body,
            headers={"Content-Type": "application/json"},
            timeout=5.0,
        )
        return resp.status_code < 500
    except Exception:
        return False


async def dispatch_with_retry(event: dict, urls: list[str]):
    body = json.dumps(event).encode()
    async with httpx.AsyncClient() as client:
        for url in urls:
            for attempt in range(1, MAX_ATTEMPTS + 1):
                ok = await _try_deliver(client, url, body)
                if ok:
                    print(f"[Delivered] {event['event']} → {url} (attempt {attempt})")
                    break
                delay = BASE_DELAY * (2 ** (attempt - 1))
                print(f"[Retry {attempt}/{MAX_ATTEMPTS}] {url} — backing off {delay:.0f}s")
                if attempt < MAX_ATTEMPTS:
                    await asyncio.sleep(delay)
            else:
                # All attempts exhausted. In production: write to a dead-letter queue.
                print(f"[Dead letter] {event['id']} → {url} gave up after {MAX_ATTEMPTS} attempts")


# ── Receiver ───────────────────────────────────────────────────────────────────

receiver_app = FastAPI()

processed_ids: set[str] = set()
processed_log: list[dict] = []

# Simulates a flaky endpoint that fails the first 2 calls, then succeeds.
_flaky_calls = 0


@receiver_app.post("/webhook")
async def receive_webhook(request: Request):
    body = await request.body()
    payload = json.loads(body)
    event_id = payload.get("id")

    if event_id in processed_ids:
        print(f"[Duplicate] {event_id} — skipping")
        return {"status": "duplicate"}

    processed_ids.add(event_id)
    processed_log.append({"id": event_id, "event": payload.get("event")})
    print(f"[Processed] {event_id}")
    return {"status": "ok"}


@receiver_app.post("/flaky")
async def flaky_endpoint(request: Request):
    global _flaky_calls
    _flaky_calls += 1

    if _flaky_calls <= 2:
        print(f"[Flaky] call #{_flaky_calls} — returning 500")
        return JSONResponse({"error": "temporary failure"}, status_code=500)

    # Succeeds on attempt 3+. Idempotency check ensures we only process once.
    body = await request.body()
    payload = json.loads(body)
    event_id = payload.get("id")

    if event_id in processed_ids:
        print(f"[Duplicate] {event_id} — skipping (flaky endpoint)")
        return {"status": "duplicate"}

    processed_ids.add(event_id)
    processed_log.append({"id": event_id, "event": payload.get("event"), "via": "flaky"})
    print(f"[Processed] {event_id} (flaky endpoint, call #{_flaky_calls})")
    return {"status": "ok"}


@receiver_app.get("/processed")
def list_processed():
    return {"count": len(processed_log), "events": processed_log}
