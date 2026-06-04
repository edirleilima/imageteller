"""API key authentication for the documentation endpoints."""
from __future__ import annotations

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery

from app.config import api

api_key_query = APIKeyQuery(name=api.api_key_name, auto_error=False)
api_key_header = APIKeyHeader(name=api.api_key_name, auto_error=False)


async def get_api_key(
    key_query: str = Security(api_key_query),
    key_header: str = Security(api_key_header),
) -> str:
    if key_query == api.api_key or key_header == api.api_key:
        return key_query or key_header
    raise HTTPException(status_code=403, detail="Could not validate credentials")
