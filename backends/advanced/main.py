from fastapi import (
    FastAPI, Request, Depends, Header, Cookie, Response,
    WebSocket, WebSocketDisconnect, BackgroundTasks, status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import (
    JSONResponse, HTMLResponse, PlainTextResponse,
    RedirectResponse, FileResponse, StreamingResponse,
)
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
from dataclasses import dataclass, field as dc_field
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import Annotated, Any
from enum import Enum
import asyncio
import base64
import secrets
import time

# ── Settings ──────────────────────────────────────────────────────────────────

class AppSettings(BaseSettings):
    app_name: str = "FastAPI Advanced"
    admin_email: str = "admin@example.com"
    items_per_page: int = 10
    debug: bool = False

    model_config = {"env_prefix": "ADV_"}

settings = AppSettings()

# ── Lifespan ──────────────────────────────────────────────────────────────────

startup_log: list[str] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_log.append(f"App started at {time.strftime('%H:%M:%S')}")
    startup_log.append(f"Loaded settings: app_name={settings.app_name}")
    yield
    startup_log.append("App shutting down")

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="FastAPI Advanced",
    description="Interactive playground for the FastAPI Advanced User Guide",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://localhost:5174",
        "http://localhost:5175", "http://localhost:5176",
        "http://127.0.0.1:5173", "http://127.0.0.1:5174",
        "http://127.0.0.1:5175", "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Middleware timing ──────────────────────────────────────────────────────────

@app.middleware("http")
async def add_process_time(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.perf_counter() - t0:.4f}s"
    return response

# ── 1. Stream Data ─────────────────────────────────────────────────────────────

@app.get("/stream/text", tags=["Stream Data"])
async def stream_text():
    async def generate():
        for i in range(8):
            yield f"chunk {i}: {'#' * (i + 1)}\n"
            await asyncio.sleep(0.25)
    return StreamingResponse(generate(), media_type="text/plain")

@app.get("/stream/sse", tags=["Stream Data"])
async def stream_sse():
    async def generate():
        for i in range(6):
            yield f"data: {{\"index\": {i}, \"value\": {i ** 2}}}\n\n"
            await asyncio.sleep(0.3)
    return StreamingResponse(generate(), media_type="text/event-stream")

# ── 2. Path Operation Advanced Configuration ───────────────────────────────────

@app.get(
    "/advanced/path-config",
    tags=["Path Operation Advanced Configuration"],
    operation_id="my_custom_operation_id",
    summary="Custom operation ID & extra OpenAPI fields",
    openapi_extra={
        "x-internal-note": "This field appears in the raw OpenAPI JSON",
    },
)
async def path_config():
    return {
        "message": "This endpoint has a custom operation_id and openapi_extra",
        "operation_id": "my_custom_operation_id",
        "tip": "Check /openapi.json to see x-internal-note in this operation",
    }

@app.get("/advanced/hidden", include_in_schema=False)
async def hidden_endpoint():
    return {"message": "I exist but don't appear in /docs or /openapi.json"}

@app.get("/advanced/schema-info", tags=["Path Operation Advanced Configuration"])
async def schema_info():
    return {
        "tip": "Try GET /advanced/hidden — it works but isn't in the OpenAPI schema",
        "docs_url": "http://localhost:8001/docs",
        "openapi_url": "http://localhost:8001/openapi.json",
    }

# ── 3. Additional Status Codes ─────────────────────────────────────────────────

store: dict[str, Any] = {"item-1": {"name": "Existing item"}}

@app.put("/advanced/items/{item_id}", tags=["Additional Status Codes"])
async def upsert_item(item_id: str, response: Response, name: str = "New item"):
    if item_id in store:
        store[item_id]["name"] = name
        return {"item_id": item_id, "name": name, "action": "updated"}
    store[item_id] = {"name": name}
    response.status_code = status.HTTP_201_CREATED
    return {"item_id": item_id, "name": name, "action": "created"}

# ── 4. Return a Response Directly ─────────────────────────────────────────────

@app.get("/advanced/response-directly/json", tags=["Return a Response Directly"])
async def response_directly_json():
    data = {"message": "Returned as JSONResponse directly", "custom_key": True}
    return JSONResponse(content=data, headers={"X-Custom": "direct-response"})

@app.get("/advanced/response-directly/xml", tags=["Return a Response Directly"])
async def response_directly_xml():
    xml = '<?xml version="1.0"?><root><message>Hello from XML</message></root>'
    return Response(content=xml, media_type="application/xml")

# ── 5. Custom Response ─────────────────────────────────────────────────────────

@app.get("/advanced/custom/html", response_class=HTMLResponse, tags=["Custom Response"])
async def custom_html():
    return """
    <html>
      <head><title>FastAPI HTML Response</title></head>
      <body style="font-family: monospace; background: #0d1117; color: #e6edf3; padding: 2rem;">
        <h1 style="color: #00d2ff;">⚡ HTMLResponse</h1>
        <p>FastAPI returned this as <code>text/html</code>.</p>
        <p>Use <code>response_class=HTMLResponse</code> on the decorator.</p>
      </body>
    </html>
    """

@app.get("/advanced/custom/text", response_class=PlainTextResponse, tags=["Custom Response"])
async def custom_text():
    return "This is a PlainTextResponse.\nContent-Type: text/plain\nNo JSON wrapping."

@app.get("/advanced/custom/redirect", tags=["Custom Response"])
async def custom_redirect():
    return RedirectResponse(url="/advanced/custom/text", status_code=302)

# ── 6. Additional Responses in OpenAPI ────────────────────────────────────────

class ItemOut(BaseModel):
    item_id: str
    name: str

class ErrorOut(BaseModel):
    detail: str

@app.get(
    "/advanced/items/{item_id}",
    response_model=ItemOut,
    responses={404: {"model": ErrorOut, "description": "Item not found"}},
    tags=["Additional Responses in OpenAPI"],
)
async def get_item(item_id: str):
    if item_id not in store:
        return JSONResponse(status_code=404, content={"detail": f"Item '{item_id}' not found"})
    return {"item_id": item_id, "name": store[item_id]["name"]}

# ── 7. Response Cookies ────────────────────────────────────────────────────────

@app.post("/advanced/cookies/set", tags=["Response Cookies"])
async def set_cookie(response: Response, value: str = "my-session-value"):
    response.set_cookie(key="session_token", value=value, httponly=True, max_age=3600)
    return {"message": f"Cookie 'session_token' set to '{value}'"}

@app.get("/advanced/cookies/read", tags=["Response Cookies"])
async def read_cookie(session_token: Annotated[str | None, Cookie()] = None):
    return {"session_token": session_token or "No cookie found — set it first"}

@app.post("/advanced/cookies/delete", tags=["Response Cookies"])
async def delete_cookie(response: Response):
    response.delete_cookie("session_token")
    return {"message": "Cookie 'session_token' deleted"}

# ── 8. Response Headers ────────────────────────────────────────────────────────

@app.get("/advanced/headers/custom", tags=["Response Headers"])
async def custom_headers(response: Response):
    response.headers["X-Custom-Header"] = "hello-from-fastapi"
    response.headers["X-Request-Id"] = secrets.token_hex(8)
    return {"message": "Check the response headers — X-Custom-Header and X-Request-Id are set"}

@app.get("/advanced/headers/from-response-object", tags=["Response Headers"])
async def headers_via_response():
    data = {"message": "Headers set via Response object before returning"}
    return JSONResponse(
        content=data,
        headers={"X-Token-Expiry": "3600", "X-App-Version": "1.0.0"},
    )

# ── 9. Response - Change Status Code ──────────────────────────────────────────

@app.get("/advanced/status/dynamic", tags=["Response - Change Status Code"])
async def dynamic_status(response: Response, found: bool = True):
    if found:
        return {"message": "Item found", "status": 200}
    response.status_code = status.HTTP_404_NOT_FOUND
    return {"message": "Item not found", "status": 404}

# ── 10. Advanced Dependencies ──────────────────────────────────────────────────

class QueryChecker:
    def __init__(self, min_length: int):
        self.min_length = min_length

    def __call__(self, q: str | None = None):
        if q and len(q) < self.min_length:
            return {"q": q, "valid": False, "reason": f"min length is {self.min_length}"}
        return {"q": q, "valid": True}

check_query_short = QueryChecker(min_length=3)
check_query_long = QueryChecker(min_length=10)

@app.get("/advanced/deps/short", tags=["Advanced Dependencies"])
async def deps_short(result: Annotated[dict, Depends(check_query_short)]):
    return {"checker": "min_length=3", "result": result}

@app.get("/advanced/deps/long", tags=["Advanced Dependencies"])
async def deps_long(result: Annotated[dict, Depends(check_query_long)]):
    return {"checker": "min_length=10", "result": result}

# ── 11. HTTP Basic Auth ────────────────────────────────────────────────────────

security = HTTPBasic()

@app.get("/advanced/basic-auth", tags=["HTTP Basic Auth"])
async def basic_auth(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    correct_user = secrets.compare_digest(credentials.username.encode(), b"admin")
    correct_pass = secrets.compare_digest(credentials.password.encode(), b"password123")
    if not (correct_user and correct_pass):
        return JSONResponse(
            status_code=401,
            content={"detail": "Incorrect credentials (try admin / password123)"},
            headers={"WWW-Authenticate": "Basic"},
        )
    return {"username": credentials.username, "message": "Authenticated via HTTP Basic Auth"}

# ── 12. Using the Request Directly ────────────────────────────────────────────

@app.get("/advanced/request-info", tags=["Using the Request Directly"])
async def request_info(request: Request):
    return {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "headers": {
            k: v for k, v in request.headers.items()
            if k.lower() in ("user-agent", "accept", "host", "referer")
        },
        "client": {"host": request.client.host, "port": request.client.port} if request.client else None,
    }

@app.post("/advanced/request-body-bytes", tags=["Using the Request Directly"])
async def request_body_bytes(request: Request):
    body = await request.body()
    return {"body_bytes": len(body), "body_preview": body[:100].decode(errors="replace")}

# ── 13. Using Dataclasses ─────────────────────────────────────────────────────

@dataclass
class DataclassItem:
    name: str
    price: float
    tags: list[str] = dc_field(default_factory=list)
    description: str | None = None

@app.post("/advanced/dataclasses/item", tags=["Using Dataclasses"])
async def create_dataclass_item(item: DataclassItem):
    return item

@app.get("/advanced/dataclasses/items", tags=["Using Dataclasses"])
async def list_dataclass_items() -> list[DataclassItem]:
    return [
        DataclassItem(name="Foo", price=9.99, tags=["a", "b"]),
        DataclassItem(name="Bar", price=14.5, description="A bar item"),
    ]

# ── 14. Advanced Middleware ────────────────────────────────────────────────────

@app.get("/advanced/middleware/info", tags=["Advanced Middleware"])
async def middleware_info(request: Request):
    return {
        "message": "This app uses @app.middleware('http') to inject X-Process-Time into every response",
        "x_process_time_header": request.headers.get("x-process-time", "set on response, not request"),
        "tip": "Check the response headers for X-Process-Time",
        "gzip_note": "GZipMiddleware can be added with: app.add_middleware(GZipMiddleware, minimum_size=1000)",
    }

# ── 15. Sub Applications ──────────────────────────────────────────────────────

subapp = FastAPI(title="Sub Application")

@subapp.get("/")
async def subapp_root():
    return {"message": "Hello from the sub-application!"}

app.mount("/subapp", subapp)

@app.get("/advanced/sub-applications/info", tags=["Sub Applications"])
async def sub_app_info():
    return {
        "message": "A sub-app is mounted at /subapp",
        "sub_app_url": "http://localhost:8001/subapp/",
        "sub_app_docs": "http://localhost:8001/subapp/docs",
        "tip": "Sub-apps have their own OpenAPI schema and /docs",
    }

# ── 16. Lifespan Events ───────────────────────────────────────────────────────

@app.get("/advanced/lifespan/log", tags=["Lifespan Events"])
async def lifespan_log():
    return {"startup_log": startup_log}

# ── 17. WebSockets ────────────────────────────────────────────────────────────

active_connections: list[WebSocket] = []

@app.websocket("/ws/echo")
async def ws_echo(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"echo: {data}")
    except WebSocketDisconnect:
        pass

@app.websocket("/ws/counter")
async def ws_counter(websocket: WebSocket):
    await websocket.accept()
    try:
        for i in range(10):
            await websocket.send_json({"count": i, "square": i * i})
            await asyncio.sleep(0.5)
        await websocket.send_json({"done": True})
    except WebSocketDisconnect:
        pass

@app.get("/advanced/websockets/info", tags=["WebSockets"])
async def ws_info():
    return {
        "echo_ws": "ws://localhost:8001/ws/echo",
        "counter_ws": "ws://localhost:8001/ws/counter",
        "tip": "Use the WebSocket playground below to connect",
    }

# ── 18. Settings and Environment Variables ────────────────────────────────────

@app.get("/advanced/settings", tags=["Settings and Environment Variables"])
async def get_settings():
    return {
        "app_name": settings.app_name,
        "admin_email": settings.admin_email,
        "items_per_page": settings.items_per_page,
        "debug": settings.debug,
        "tip": "Override with env vars: ADV_APP_NAME='My App' uvicorn ...",
    }

# ── 19. JSON with Bytes as Base64 ─────────────────────────────────────────────

class ItemWithBytes(BaseModel):
    name: str
    data: bytes

@app.post("/advanced/base64/encode", tags=["JSON with Bytes as Base64"])
async def encode_bytes(item: ItemWithBytes):
    encoded = base64.b64encode(item.data).decode()
    return {"name": item.name, "data_base64": encoded, "data_length": len(item.data)}

@app.post("/advanced/base64/round-trip", tags=["JSON with Bytes as Base64"])
async def bytes_round_trip(item: ItemWithBytes):
    json_data = jsonable_encoder(item)
    return {
        "original_name": item.name,
        "json_encoded": json_data,
        "note": "FastAPI/Pydantic encodes bytes as base64 in JSON automatically",
    }

# ── 20. OpenAPI Webhooks ──────────────────────────────────────────────────────

@app.get("/advanced/webhooks/info", tags=["OpenAPI Webhooks"])
async def webhooks_info():
    return {
        "message": "Webhooks are declared in the FastAPI() constructor with webhooks=",
        "example": "They appear in /openapi.json under 'webhooks' key",
        "tip": "Check https://fastapi.tiangolo.com/advanced/openapi-webhooks/ for full example",
    }

# ── 21. Behind a Proxy ────────────────────────────────────────────────────────

@app.get("/advanced/proxy/info", tags=["Behind a Proxy"])
async def proxy_info(request: Request):
    return {
        "message": "When behind a proxy, set root_path so OpenAPI schema URLs are correct",
        "current_root_path": request.scope.get("root_path", ""),
        "tip": "Use: uvicorn main:app --root-path /api/v1",
        "forwarded_headers": {
            k: v for k, v in request.headers.items()
            if "forwarded" in k.lower() or "x-real" in k.lower()
        },
    }

# ── 22. OpenAPI Callbacks ─────────────────────────────────────────────────────

@app.get("/advanced/callbacks/info", tags=["OpenAPI Callbacks"])
async def callbacks_info():
    return {
        "message": "Callbacks document external HTTP requests your API makes to client URLs",
        "use_case": "e.g. a webhook you POST to when an async job finishes",
        "tip": "Declared with callbacks=[router] on the path operation decorator",
    }

# ── 23. Generating Clients ────────────────────────────────────────────────────

@app.get("/advanced/generate-clients/info", tags=["Generating Clients"])
async def generate_clients_info():
    return {
        "openapi_schema": "http://localhost:8001/openapi.json",
        "tools": ["openapi-generator", "hey-api/openapi-ts", "speakeasy"],
        "tip": "Point any OpenAPI codegen tool at /openapi.json to generate typed clients",
        "unique_names": "Use unique operation_id on each endpoint for clean generated method names",
    }

# ── 24. Advanced Python Types ─────────────────────────────────────────────────

from typing import TypeVar, Generic
T = TypeVar("T")

class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

class SimpleItem(BaseModel):
    id: int
    name: str

@app.get("/advanced/python-types/paginated", response_model=Paginated[SimpleItem], tags=["Advanced Python Types"])
async def paginated_items(page: int = 1, page_size: int = 3):
    all_items = [SimpleItem(id=i, name=f"Item {i}") for i in range(1, 11)]
    start = (page - 1) * page_size
    return Paginated(
        items=all_items[start:start + page_size],
        total=len(all_items),
        page=page,
        page_size=page_size,
    )
