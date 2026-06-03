"""
Combined Observability: Logs + Metrics + Correlation IDs
==========================================================
A production-ready FastAPI app that ties all three signals together.

The three pillars of observability
    Logs    — what happened (structured JSON, searchable by field)
    Metrics — how much / how often / how long (counters, histograms, gauges)
    Traces  — the path a single request took across services

    This file covers logs and metrics in full. Tracing across multiple
    services requires a trace backend (Jaeger, Tempo) and the OpenTelemetry
    SDK — that's a separate setup. The correlation ID here is a lightweight
    single-service trace: one ID that links every log line for one request.

Correlation IDs
    Each request gets a UUID assigned in middleware. It flows:
      • into every log line for that request (via structlog context vars)
      • back to the caller as X-Request-ID response header
      • into the Prometheus labels so you can find the metric spike
        that corresponds to a specific request in the logs

    In a multi-service setup, the caller passes its own X-Request-ID header
    and downstream services forward it. Every service logs the same ID, so
    a single query finds the request's full journey across your whole stack.

Run:
    uvicorn 03_combined:app --reload

Then exercise it:
    curl -s http://localhost:8000/orders | jq
    curl -s http://localhost:8000/orders/999 | jq    # 404
    curl -s http://localhost:8000/orders -X POST     # validation error
    curl -s http://localhost:8000/metrics            # Prometheus output
    curl -s http://localhost:8000/health             # health check

Watch logs in the terminal to see request_id threading through every line.

To run the full observability stack (Prometheus + Grafana):
    docker compose up -d
    # Prometheus: http://localhost:9090
    # Grafana:    http://localhost:3000  (admin / admin)
    # Add Prometheus data source: http://prometheus:9090
"""

import time
import uuid

import structlog
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from structlog.contextvars import bind_contextvars, clear_contextvars, merge_contextvars

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.dict_tracebacks,
        structlog.dev.ConsoleRenderer(),   # swap for JSONRenderer() in production
    ],
    wrapper_class=structlog.make_filtering_bound_logger(10),
)

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "Request duration",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)
ACTIVE_REQUESTS = Gauge("http_active_requests", "In-flight requests")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Observability Demo")


# ---------------------------------------------------------------------------
# Observability middleware — runs before every request
# ---------------------------------------------------------------------------

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    # Honour a caller-supplied ID for cross-service tracing, or generate one.
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]

    clear_contextvars()
    bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )

    log.info("request_started")
    ACTIVE_REQUESTS.inc()
    start = time.perf_counter()

    try:
        response: Response = await call_next(request)
        status = response.status_code
    except Exception as exc:
        status = 500
        log.exception("unhandled_exception", exc_info=exc)
        response = JSONResponse(status_code=500, content={"detail": "internal server error"})
    finally:
        duration = time.perf_counter() - start
        ACTIVE_REQUESTS.dec()
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=str(status),
        ).inc()
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)
        log.info("request_finished", status=status, duration_ms=round(duration * 1000, 1))

    response.headers["X-Request-ID"] = request_id
    clear_contextvars()
    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

ORDERS = {
    1: {"id": 1, "item": "keyboard", "status": "shipped"},
    2: {"id": 2, "item": "monitor",  "status": "processing"},
}


@app.get("/health")
async def health():
    """Kubernetes liveness / readiness probe target."""
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/orders")
async def list_orders():
    log.info("listing_orders", count=len(ORDERS))
    return list(ORDERS.values())


@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    order = ORDERS.get(order_id)
    if not order:
        log.warning("order_not_found", order_id=order_id)
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    log.info("order_fetched", order_id=order_id, order_status=order["status"])
    return order
