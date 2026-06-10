"""
01_receiver.py — The Receiver Side

A webhook is just an HTTP POST that someone else sends to your server.
When GitHub merges a PR, when Stripe processes a payment, when Twilio
delivers an SMS — they all fire a POST to a URL you give them.

Your job as the receiver:
  1. Accept the POST
  2. Return a 2xx response FAST (before doing any real work)
  3. Do the actual work asynchronously (or queue it)

Why respond fast? Senders have short timeouts (5–30s). If you take too
long processing, they'll assume delivery failed and retry — sending you
the same event again.

Run:
    uvicorn 01_receiver:app --port 8001 --reload

Test:
    curl -X POST http://localhost:8001/webhook \\
      -H "Content-Type: application/json" \\
      -d '{"event": "order.created", "id": "evt_001", "data": {"order_id": 42}}'

    curl http://localhost:8001/events
"""

import asyncio
import json
from datetime import datetime, timezone

from fastapi import FastAPI, Request

app = FastAPI()

received_events: list[dict] = []


@app.post("/webhook")
async def receive_webhook(request: Request):
    body = await request.body()
    payload = json.loads(body)

    received_events.append({
        "received_at": datetime.now(timezone.utc).isoformat(),
        "event": payload.get("event"),
        "id": payload.get("id"),
        "payload": payload,
    })

    print(f"[Received] {payload.get('event')} id={payload.get('id')}")

    # Kick off real work without blocking the response.
    # In production: publish to a queue (Redis, SQS) instead of a task.
    asyncio.create_task(process_event(payload))

    return {"status": "accepted"}


async def process_event(payload: dict):
    await asyncio.sleep(0)  # yield, then do work
    print(f"[Processing] {payload.get('event')}: {payload.get('data')}")


@app.get("/events")
def list_events():
    return received_events
