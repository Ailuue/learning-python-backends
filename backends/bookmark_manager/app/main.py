import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database import create_db_and_tables
from app.exceptions import register_exception_handlers
from app.logging_config import configure_logging
from app.rate_limit import limiter
from app.routers import auth, bookmarks, categories, tags

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting bookmark manager API")
    create_db_and_tables()
    yield
    logger.info("Shutting down bookmark manager API")


settings = get_settings()

app = FastAPI(
    title="Bookmark Manager API",
    version="0.1.0",
    description="A bookmark manager with JWT auth, tags, and categories.",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
