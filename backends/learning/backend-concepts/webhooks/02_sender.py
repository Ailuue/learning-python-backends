"""
02_sender.py — The Sender Side

Now we're on the other side: our service fires webhooks whenever
something interesting happens.

The pattern:
  1. Consumers register a URL with us ("call me at this endpoint")
  2. When an event occurs, we POST to every registered URL
  3. We don't block the main request on webhook delivery

Run (with 01_receiver.py already running on port 8001):
    uvicorn 02_sender:app --port 8000 --reload

Then register the receiver and trigger an event:
    # Register 01_receiver as a listener
    curl -X POST "http://localhost:8000/webhooks/register?url=http://localhost:8001/webhook"

    # Create an order — this fires a webhook to all registered URLs
    curl -X POST "http://localhost:8000/orders?item=keyboard"

    # Check what the receiver got
    curl http://localhost:8001/events
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI

app = FastAPI()

registered_urls: list[str] = []


@app.post("/webhooks/register")
def register_webhook(url: str):
    if url not in registered_urls:
        registered_urls.append(url)
    return {"registered": url, "total_registered": len(registered_urls)}


@app.get("/webhooks")
def list_webhooks():
    return registered_urls


@app.post("/orders")
async def create_order(item: str):
    order_id = uuid.uuid4().hex[:8]

    event = {
        "id": f"evt_{uuid.uuid4().hex[:12]}",
        "event": "order.created",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"order_id": order_id, "item": item},
    }

    # Fire and forget — the response doesn't wait for webhook delivery.
    asyncio.create_task(dispatch_webhooks(event))

    return {"order_id": order_id, "status": "created"}


async def dispatch_webhooks(event: dict):
    body = json.dumps(event).encode()
    async with httpx.AsyncClient() as client:
        for url in registered_urls:
            try:
                resp = await client.post(
                    url,
                    content=body,
                    headers={"Content-Type": "application/json"},
                    timeout=5.0,
                )
                print(f"[Dispatched] {event['event']} → {url} ({resp.status_code})")
            except Exception as e:
                print(f"[Dispatch failed] {url}: {e}")
