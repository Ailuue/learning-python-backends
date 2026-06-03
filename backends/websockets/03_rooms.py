"""
WebSocket Rooms
================
Clients join a named room via the URL path. Messages only broadcast to
other clients in the same room. This models Slack channels, game lobbies,
or any segmented broadcast scenario.

    Client A → ws://localhost:8000/ws/general?username=alice
    Client B → ws://localhost:8000/ws/general?username=bob
    Client C → ws://localhost:8000/ws/dev?username=carol

    Alice sends "hello":
      → Bob receives it       (same room: general)
      → Carol does NOT        (different room: dev)

The room is a dict[str, list[WebSocket]]. This is still per-process —
the same single-process limitation as 02_broadcast.py applies here.
The standard production fix is Redis pub/sub:
  - client joins room → server subscribes to Redis channel "room:{name}"
  - client sends message → server publishes to that channel
  - all server processes subscribed to that channel receive it and forward
    to their local sockets

Run:
    uvicorn 03_rooms:app --reload

Test: open static/chat.html in multiple tabs:
  Tab 1: connect to ws://localhost:8000/ws/general?username=alice
  Tab 2: connect to ws://localhost:8000/ws/general?username=bob
  Tab 3: connect to ws://localhost:8000/ws/dev?username=carol
  → alice and bob see each other's messages; carol is isolated in #dev
"""

from collections import defaultdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


class RoomManager:
    def __init__(self):
        self.rooms: dict[str, list[WebSocket]] = defaultdict(list)

    async def join(self, room: str, ws: WebSocket) -> None:
        await ws.accept()
        self.rooms[room].append(ws)
        print(f"  + [{room}] client joined   (room size: {len(self.rooms[room])})")

    def leave(self, room: str, ws: WebSocket) -> None:
        if ws in self.rooms[room]:
            self.rooms[room].remove(ws)
        print(f"  - [{room}] client left   (room size: {len(self.rooms[room])})")

    async def broadcast(self, room: str, message: str) -> None:
        dead: list[WebSocket] = []
        for ws in self.rooms[room]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.leave(room, ws)


manager = RoomManager()


@app.websocket("/ws/{room}")
async def room_endpoint(websocket: WebSocket, room: str, username: str = "anonymous"):
    await manager.join(room, websocket)
    await manager.broadcast(room, f"*** {username} joined #{room} ***")
    try:
        while True:
            text = await websocket.receive_text()
            await manager.broadcast(room, f"[{username}] {text}")
    except WebSocketDisconnect:
        manager.leave(room, websocket)
        await manager.broadcast(room, f"*** {username} left #{room} ***")
