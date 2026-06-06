"""
WebSocket Basics: Echo Server
==============================
WebSockets provide a persistent, bidirectional channel over a single TCP
connection. Unlike HTTP, either side can send a message at any time without
waiting for a request/response cycle.

    Client                           Server
      │                                │
      │──── HTTP Upgrade request ─────▶│
      │◀─── 101 Switching Protocols ───│   (handshake, one-time)
      │                                │
      │──── "hello" ──────────────────▶│
      │◀─── "Echo: hello" ─────────────│
      │                                │
      │──── "world" ──────────────────▶│
      │◀─── "Echo: world" ─────────────│
      │                                │
      │──── close ────────────────────▶│
      │◀─── close ─────────────────────│

Connection lifecycle:
  1. websocket.accept()    — completes the HTTP→WS upgrade handshake
  2. receive_text() loop   — blocks until the client sends something
  3. WebSocketDisconnect   — raised when the client closes the connection

Run:
    uvicorn 01_echo:app --reload

Test with curl-like one-liner:
    python -c "
    import asyncio, websockets
    async def t():
        async with websockets.connect('ws://localhost:8000/ws') as ws:
            for msg in ['hello', 'world', 'done']:
                await ws.send(msg)
                print(await ws.recv())
    asyncio.run(t())
    "

Or open static/chat.html in a browser and connect to ws://localhost:8000/ws.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


@app.websocket("/ws")
async def websocket_echo(websocket: WebSocket):
    await websocket.accept()
    client = websocket.client
    print(f"Client connected: {client}")

    try:
        while True:
            message = await websocket.receive_text()
            print(f"  ← received: {message!r}")
            reply = f"Echo: {message}"
            await websocket.send_text(reply)
            print(f"  → sent:     {reply!r}")
    except WebSocketDisconnect:
        print(f"Client disconnected: {client}")
