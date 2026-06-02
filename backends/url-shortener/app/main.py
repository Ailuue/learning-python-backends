from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import cache
from app.database import Base, engine
from app.routers import auth, redirect, urls


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await cache.init()
    yield
    await cache.close()
    await engine.dispose()


app = FastAPI(title="URL Shortener API", version="1.0.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(urls.router)
app.include_router(redirect.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "cache": await cache.stats()}
