"""
Prometheus Metrics
===================
Prometheus scrapes an HTTP /metrics endpoint on a schedule (e.g. every 15s)
and stores time-series data. Grafana then queries Prometheus to build dashboards.

The four metric types
    Counter   — monotonically increasing. Never resets (except process restart).
                Use for: total requests, total errors, total bytes sent.
                Query: rate(counter[5m]) → per-second rate over last 5 minutes.

    Histogram — samples observations into configurable buckets, exposing:
                *_bucket{le="0.1"} → requests completed in ≤100ms
                *_sum               → total sum of all observed values
                *_count             → total number of observations
                Use for: request durations, payload sizes.
                Query: histogram_quantile(0.95, rate(*_bucket[5m])) → p95 latency.

    Gauge     — current value, can go up or down.
                Use for: active connections, queue depth, cache size.
                Query: the raw gauge value.

    Summary   — like Histogram but computes quantiles client-side. Less flexible
                (no cross-instance aggregation), rarely preferred over Histogram.

Labels
    Labels are key-value pairs on a metric. They let you slice and dice:
        http_requests_total{method="GET", endpoint="/search", status="200"}
    Keep label cardinality low — don't use user IDs or UUIDs as labels.
    High cardinality explodes storage and query time.

Run:
    uvicorn 02_metrics:app --reload

Inspect:
    curl http://localhost:8000/metrics           # raw Prometheus text format
    curl http://localhost:8000/slow             # generates duration samples
    curl http://localhost:8000/error            # generates error counter samples
"""

import asyncio
import random
import time

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

app = FastAPI()

# ---------------------------------------------------------------------------
# Metric definitions — define once at module level, reference everywhere
# ---------------------------------------------------------------------------

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],   # label names
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    # Buckets tuned for a web API. Adjust for your SLOs.
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Number of HTTP requests currently being processed",
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP errors (4xx and 5xx)",
    ["method", "endpoint", "status"],
)


# ---------------------------------------------------------------------------
# Middleware — records metrics for every request automatically
# ---------------------------------------------------------------------------

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    method = request.method
    endpoint = request.url.path

    # Gauge: increment on entry, decrement on exit (even if exception)
    ACTIVE_REQUESTS.inc()
    start = time.perf_counter()

    # Bound before the try so `finally` is safe even when an exception — including
    # a BaseException like asyncio.CancelledError on client disconnect — means
    # the assignment below never runs. An unhandled request is a 500.
    status = "500"

    try:
        response: Response = await call_next(request)
        status = str(response.status_code)
    finally:
        duration = time.perf_counter() - start
        ACTIVE_REQUESTS.dec()

        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

        # `finally` is the single place errors are counted — counting them in an
        # `except` branch as well would double-count every unhandled exception.
        if status.startswith(("4", "5")) and status != "404":
            ERROR_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()

    return response


# ---------------------------------------------------------------------------
# /metrics endpoint — Prometheus scrapes this
# ---------------------------------------------------------------------------

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------------------------
# Demo routes — generate varied metric data
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/fast")
async def fast():
    """Always fast — generates low-latency histogram samples."""
    await asyncio.sleep(random.uniform(0.001, 0.005))
    return {"latency": "low"}


@app.get("/slow")
async def slow():
    """Intentionally slow — pushes samples into the 0.5–2.5s buckets."""
    await asyncio.sleep(random.uniform(0.5, 1.5))
    return {"latency": "high"}


@app.get("/error")
async def error():
    """Always 500 — increments the error counter."""
    return Response(status_code=500, content="simulated error")


@app.get("/random")
async def rand():
    """Variable latency and occasional errors — realistic traffic simulation."""
    await asyncio.sleep(random.uniform(0.01, 0.3))
    if random.random() < 0.1:   # 10% error rate
        return Response(status_code=500, content="random error")
    return {"value": random.randint(1, 100)}
