# WebSockets & Server-Sent Events

## What is this?

When you load a web page, your browser sends an HTTP request and the server sends back a response. That's it — the connection closes. If you want new data (say, a new chat message arrived), your browser has to ask again. And again. And again.

**WebSockets** solve this by keeping the connection open after the initial handshake. Either side — the browser or the server — can send a message at any time, instantly, without a new request. This is how chat apps, live sports scores, collaborative editors, and multiplayer games work.

**Server-Sent Events (SSE)** are a simpler alternative for when data only needs to flow one way: server → browser. Think live logs, notification feeds, or a stock ticker. The browser opens one HTTP connection and the server just keeps writing to it.

## When would you use this?

| Scenario | Best fit |
|---|---|
| Chat, multiplayer game, collaborative editing | WebSocket (bidirectional) |
| Live dashboard, notifications, log stream | SSE (server → client only) |
| Polling every few seconds for updates | Either — but you probably shouldn't be polling |

If your users are staring at a screen waiting for something to happen, you probably want one of these.

## What the files cover

| File | What it teaches |
|---|---|
| `01_echo.py` | The basics: how a WebSocket connection is opened, kept alive, and closed |
| `02_broadcast.py` | A chat room: one message arrives, everyone gets it |
| `03_rooms.py` | Named channels: messages only reach people in the same room |
| `04_sse.py` | SSE: a server that streams data continuously without the client asking |
| `static/chat.html` | Browser test UI for files 02 and 03 |
| `static/sse.html` | Browser test UI for file 04 |

## How to run

```bash
pip install -r requirements.txt

# Pick a file and run it with uvicorn:
uvicorn 01_echo:app --reload
uvicorn 02_broadcast:app --reload
uvicorn 03_rooms:app --reload
uvicorn 04_sse:app --reload

# Then open static/chat.html or static/sse.html in your browser.
# For 01_echo.py you can also test from the terminal:
python -c "
import asyncio, websockets
async def t():
    async with websockets.connect('ws://localhost:8000/ws') as ws:
        await ws.send('hello')
        print(await ws.recv())
asyncio.run(t())
"
```
