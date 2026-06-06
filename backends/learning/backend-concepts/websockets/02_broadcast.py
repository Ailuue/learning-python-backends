"""
WebSocket Broadcast: Chat Room
================================
A ConnectionManager tracks every connected client and broadcasts to all of
them at once. This is the foundation of any multi-user real-time feature:
chat, live dashboards, collaborative cursors.

    Client A ──▶ "hello" ──▶ Server ──▶ "hello" ──▶ Client A
                                     └──▶ "hello" ──▶ Client B
                                     └──▶ "hello" ──▶ Client C

Key concern: detecting stale connections.
  A client can drop without sending a close frame (browser crash, network cut).
  The server only discovers this when it next tries to send — the send raises
  an exception. We catch that, remove the dead socket, and continue broadcasting
  to the remaining clients.

Key concern: this dict lives in one process.
  Multiple uvicorn workers or multiple containers each have their own
  ConnectionManager. In production, back the broadcast with Redis pub/sub so
  a message sent to any process reaches all clients regardless of which
  worker they landed on.

Run:
    uvicorn 02_broadcast:app --reload

Test: open static/chat.html in two browser tabs, connect both to
      ws://localhost:8000/ws, and send messages from either tab.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)
        print(f"  + client connected   (total: {len(self.active)})")

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active:
            self.active.remove(ws)
        print(f"  - client disconnected  (total: {len(self.active)})")

    async def broadcast(self, message: str) -> None:
        dead: list[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)   # found a stale connection mid-broadcast
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@app.websocket("/ws")
async def chat_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            text = await websocket.receive_text()
            print(f"  message: {text!r}")
            await manager.broadcast(text)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
