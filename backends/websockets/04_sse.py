"""
Server-Sent Events (SSE)
=========================
SSE is a simpler, HTTP-based alternative to WebSockets for push-only scenarios.
The server streams newline-delimited text; the client cannot send data back
through the same connection. The browser's built-in EventSource API handles
reconnection automatically.

    When to use SSE vs WebSockets
    ─────────────────────────────
    SSE                                    WebSockets
    ────────────────────────────────────   ────────────────────────────────────
    Server → client only                   Bidirectional
    Plain HTTP/1.1 (proxy-friendly)        Requires WS-aware proxy config
    EventSource reconnects automatically   Must implement reconnect yourself
    Great for: feeds, logs, dashboards     Great for: chat, games, collab edits

SSE wire format — each event is separated by a blank line:

    data: {"temperature": 21.4}\n
    \n
    data: {"temperature": 21.6}\n
    \n
    event: done\n
    data: finished\n
    \n

  Named events (event: <name>) let the client listen for specific event types,
  e.g. EventSource.addEventListener("done", handler).

Run:
    uvicorn 04_sse:app --reload

Test in terminal:
    curl -N http://localhost:8000/stream/temperature
    curl -N http://localhost:8000/stream/deploy-log

Or open static/sse.html in a browser.
"""

import asyncio
import random
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()


async def temperature_stream():
    """Simulates a sensor that emits readings every second."""
    temp = 20.0
    while True:
        temp += random.uniform(-0.3, 0.3)
        ts = datetime.now(timezone.utc).isoformat()
        payload = f'{{"temperature": {temp:.1f}, "timestamp": "{ts}"}}'
        yield f"data: {payload}\n\n"
        await asyncio.sleep(1)


async def deploy_log_stream():
    """
    Simulates a live deployment log. Uses a named 'done' event so the
    client can detect completion separately from regular data events.
    """
    steps = [
        "Pulling Docker image...",
        "Running database migrations...",
        "Seeding fixtures...",
        "Starting application server...",
        "Health check: GET /health → 200 OK",
        "Deployment complete.",
    ]
    for step in steps:
        yield f"data: {step}\n\n"
        await asyncio.sleep(0.8)

    # Named event — the client can register a specific listener for "done"
    yield "event: done\ndata: finished\n\n"


def sse_response(generator) -> StreamingResponse:
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # tells nginx not to buffer this response
        },
    )


@app.get("/stream/temperature")
async def stream_temperature():
    return sse_response(temperature_stream())


@app.get("/stream/deploy-log")
async def stream_deploy_log():
    return sse_response(deploy_log_stream())
