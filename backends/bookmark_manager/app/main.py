import logging
from contextlib import asynccontextmanager
from typing import Callable, cast

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.exceptions import register_exception_handlers
from app.logging_config import configure_logging
from app.rate_limit import limiter
from app.routers import auth, bookmarks, categories, tags

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting bookmark manager API")
    # Schema is managed by Alembic: `alembic upgrade head` before starting the app.
    yield
    logger.info("Shutting down bookmark manager API")


settings = get_settings()

# OpenAPI tag metadata — renders as section headers + descriptions in /docs and /redoc.
# The `name` here must match the `tags=[...]` used on each router/path operation.
# Order in this list controls the order of sections in the docs.
tags_metadata = [
    {
        "name": "auth",
        "description": (
            "User registration, login (OAuth2 password flow), logout, and current-user "
            "lookup. Logout adds the token's `jti` to a Redis blocklist for the "
            "remainder of its lifetime."
        ),
    },
    {
        "name": "bookmarks",
        "description": (
            "Create, list, update, and delete bookmarks. Includes a click-tracking "
            "endpoint that increments a Redis counter; counts are flushed to the "
            "database every 10 minutes by a Celery Beat task (write-behind cache)."
        ),
    },
    {
        "name": "categories",
        "description": "User-scoped folders for organizing bookmarks.",
    },
    {
        "name": "tags",
        "description": (
            "User-scoped tags. Created implicitly when bookmarks are saved with new "
            "tag names; can also be listed and deleted directly."
        ),
    },
    {
        "name": "meta",
        "description": "Health checks and service metadata.",
    },
]

app = FastAPI(
    title="Bookmark Manager API",
    version="0.1.0",
    description=(
        "A bookmark manager with JWT auth, tag/category organization, "
        "Redis-backed rate limiting, Celery background tasks, and a write-behind "
        "click counter."
    ),
    openapi_tags=tags_metadata,
    contact={"name": "Alex"},
    lifespan=lifespan,
)

app.state.limiter = limiter
# Cast to handle contravariance of exception handler signature: FastAPI expects a handler that takes
# (Request, Exception) but _rate_limit_exceeded_handler is typed as (Request, RateLimitExceeded).
casted_handler = cast(
    Callable[[Request, Exception], Response], _rate_limit_exceeded_handler
)
app.add_exception_handler(RateLimitExceeded, casted_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(bookmarks.router)
app.include_router(tags.router)
app.include_router(categories.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "environment": settings.environment}
