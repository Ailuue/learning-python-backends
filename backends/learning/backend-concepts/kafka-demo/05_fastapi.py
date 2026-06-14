"""
FastAPI Event Producer
========================
HTTP requests publish events to Kafka. The API returns immediately;
a separate worker process consumes and processes the events asynchronously.

This is the event-driven decoupling pattern:

    Browser ──POST /orders──▶ FastAPI ──▶ Kafka topic: "order.placed"
                              returns 202 Accepted immediately
                                               │
                                               ▼
                                          worker.py
                                          (separate process)
                                          - validates order
                                          - charges payment
                                          - sends confirmation email
                                          - updates inventory

Why decouple with Kafka instead of doing it all in the request?
    • The HTTP request returns fast regardless of how long processing takes.
    • If the worker is down, events queue up in Kafka and process on restart.
    • You can scale workers independently of API servers.
    • Multiple workers (different consumer groups) can react to the same event.

Run:
    Terminal 1:  docker compose up -d
    Terminal 2:  uvicorn 05_fastapi:app --reload
    Terminal 3:  python worker.py

    Then:
    curl -s -X POST http://localhost:8000/orders \\
      -H "Content-Type: application/json" \\
      -d '{"item": "keyboard", "quantity": 2, "customer_id": "cust-42"}' | jq

    Watch terminal 3 — the worker processes the event asynchronously.
"""

import json
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from pydantic import BaseModel

BOOTSTRAP = "localhost:9092"
ORDERS_TOPIC = "order.placed"

producer: KafkaProducer | None = None


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer
    try:
        producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode(),
            key_serializer=lambda k: k.encode() if k else None,
            acks="all",
            retries=3,
        )
        print("Kafka producer connected.")
    except NoBrokersAvailable:
        print("WARNING: Kafka not available — events will not be published.")
    yield
    if producer:
        producer.flush()
        producer.close()


app = FastAPI(title="Order API", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class OrderRequest(BaseModel):
    item: str
    quantity: int
    customer_id: str


class OrderResponse(BaseModel):
    order_id: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/orders", response_model=OrderResponse, status_code=202)
async def create_order(req: OrderRequest):
    """
    Creates an order record and publishes an event to Kafka.
    Returns 202 Accepted immediately — processing happens asynchronously.
    """
    order_id = str(uuid.uuid4())[:8]
    event = {
        "order_id":    order_id,
        "item":        req.item,
        "quantity":    req.quantity,
        "customer_id": req.customer_id,
        "created_at":  time.time(),
    }

    if producer:
        # Key by customer_id so all events for a customer go to the same partition.
        producer.send(ORDERS_TOPIC, key=req.customer_id, value=event)
        # Don't flush here — let Kafka batch messages for throughput.
        # The lifespan shutdown handler flushes on graceful stop.
    else:
        print(f"[no kafka] would publish: {event}")

    return OrderResponse(
        order_id=order_id,
        status="accepted",
        message="Order received. Processing asynchronously.",
    )


@app.get("/health")
async def health():
    return {"status": "ok", "kafka_connected": producer is not None}
