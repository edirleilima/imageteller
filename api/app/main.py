"""ImageTeller API entry point."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import api
from app.media.comfyui import image_generation_worker
from app.ratelimit import limiter
from app.routers import docs, stories, images


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the background image-generation worker; cancel it on shutdown."""
    worker = asyncio.create_task(image_generation_worker())
    try:
        yield
    finally:
        worker.cancel()


app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[api.domain_url] if api.domain_url else [],
    allow_credentials=False,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["Content-Type", "X-User-Id"],
)

app.include_router(docs.router)
app.include_router(stories.router)
app.include_router(images.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
