"""
Structured Logging with structlog
===================================
Plain text logs are hard to query at scale. Structured logs emit JSON so
aggregators (Datadog, Loki, CloudWatch Insights) can index every field.

    Plain text:
        2024-01-15 10:23:45 ERROR Failed to process order 12345 for user 99

    Structured JSON:
        {"timestamp": "2024-01-15T10:23:45Z", "level": "error",
         "event": "order_processing_failed", "order_id": 12345,
         "user_id": 99, "duration_ms": 142, "error": "InsufficientFunds"}

    Why JSON wins:
        level=error AND order_id=12345   → instant query in any log system
        user_id=99                       → full history of one user's activity

Processors pipeline
    structlog transforms each log event through a list of processors before
    rendering. Each processor receives the event dict and returns a modified
    version. This is where you add timestamps, log levels, redaction, etc.

        Event dict → [add_log_level] → [TimeStamper] → [JSONRenderer] → output

Bound logger
    log.bind(key=value) returns a new logger that automatically includes
    those keys on every subsequent call. Use it to attach request-scoped
    context (request_id, user_id) once, then log normally throughout.

Context variables
    bind_contextvars() sets async-safe context (like thread-local, but for
    coroutines). Any logger created in the same async task picks up those
    vars automatically. This is the right tool for per-request context in
    FastAPI/asyncio because each request runs in its own coroutine.

Run:
    python 01_structured_logging.py
"""

import asyncio
import uuid

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars, merge_contextvars

# ---------------------------------------------------------------------------
# Configuration — call once at application startup
# ---------------------------------------------------------------------------

def configure_for_production():
    """JSON output — machine-readable, for log aggregators."""
    structlog.configure(
        processors=[
            merge_contextvars,                          # inject context vars
            structlog.stdlib.add_log_level,             # adds "level" key
            structlog.processors.TimeStamper(fmt="iso"),# adds "timestamp" key
            structlog.processors.dict_tracebacks,       # format exceptions
            structlog.processors.JSONRenderer(),        # final JSON string
        ],
        wrapper_class=structlog.make_filtering_bound_logger(10),  # DEBUG+
    )


def configure_for_development():
    """Human-readable coloured output for local development."""
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            structlog.dev.ConsoleRenderer(),            # coloured key=value output
        ],
        wrapper_class=structlog.make_filtering_bound_logger(10),
    )


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

async def simulate_request(path: str, user_id: int, fail: bool = False):
    """Simulates a single HTTP request lifecycle."""
    # bind_contextvars sets context for THIS coroutine only.
    # Every log line below automatically includes request_id and user_id.
    clear_contextvars()
    bind_contextvars(request_id=str(uuid.uuid4())[:8], user_id=user_id, path=path)

    log = structlog.get_logger()
    log.info("request_received")

    if fail:
        log.error("db_query_failed", table="orders", error="connection timeout")
        log.warning("request_failed", status=500)
    else:
        log.debug("db_query", table="orders", rows_returned=3, duration_ms=8)
        log.info("request_completed", status=200, duration_ms=22)

    clear_contextvars()


def demo_bound_logger():
    log = structlog.get_logger()

    print("\n--- 1. Basic logging ---")
    log.info("server_started", port=8000, env="production")
    log.warning("high_memory", used_mb=3800, limit_mb=4000)

    print("\n--- 2. Bound logger: attach context once ---")
    # Every call on this logger includes order_id and customer automatically.
    order_log = log.bind(order_id=99123, customer="alice@example.com")
    order_log.info("payment_initiated", amount=49.99, currency="USD")
    order_log.info("payment_captured", provider="stripe")
    order_log.info("order_fulfilled", warehouse="EU-1")
    # The original log is unchanged — bind returns a new logger.
    log.info("unrelated_event")

    print("\n--- 3. Nested binding: add more context later ---")
    base = log.bind(service="checkout")
    with_user = base.bind(user_id=42)
    with_user.info("cart_submitted", items=3)
    with_user.bind(order_id=99124).info("order_created")


async def demo_context_vars():
    print("\n--- 4. Context variables: async-safe per-coroutine context ---")
    # Run two requests concurrently — their context vars stay separate.
    await asyncio.gather(
        simulate_request("/api/orders", user_id=1),
        simulate_request("/api/products", user_id=2),
        simulate_request("/api/checkout", user_id=3, fail=True),
    )


def main():
    print("=== Structured Logging Demo ===\n")

    print("[ Development mode: human-readable output ]")
    configure_for_development()
    demo_bound_logger()
    asyncio.run(demo_context_vars())

    print("\n\n[ Production mode: JSON output ]")
    configure_for_production()
    demo_bound_logger()
    asyncio.run(demo_context_vars())


if __name__ == "__main__":
    main()
