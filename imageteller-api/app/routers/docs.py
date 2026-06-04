"""Authenticated /docs, /redoc, and /openapi.json."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from app.config import api
from app.security import get_api_key

router = APIRouter()


@router.get("/docs", include_in_schema=False)
async def get_swagger_documentation(api_key: str = Depends(get_api_key)):
    return get_swagger_ui_html(
        openapi_url=f"{api.root_path}/openapi.json?{api.api_key_name}={api_key}",
        title="docs",
    )


@router.get("/redoc", include_in_schema=False)
async def get_redoc_documentation(api_key: str = Depends(get_api_key)):
    return get_redoc_html(
        openapi_url=f"{api.root_path}/openapi.json?{api.api_key_name}={api_key}",
        title="redoc",
    )


@router.get("/openapi.json", include_in_schema=False)
async def openapi(request: Request, api_key: str = Depends(get_api_key)):
    return request.app.openapi()
