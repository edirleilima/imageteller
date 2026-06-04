"""ImageTeller API entry point."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import urllib3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import api
from app.media.comfyui import image_generation_worker
from app.routers import docs, stories, images

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the background image-generation worker; cancel it on shutdown."""
    worker = asyncio.create_task(image_generation_worker())
    try:
        yield
    finally:
        worker.cancel()


app = FastAPI(
    root_path=api.root_path,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[api.domain_url] if api.domain_url else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(docs.router)
app.include_router(stories.router)
app.include_router(images.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
