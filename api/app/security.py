"""Authentication / identity helpers.

``get_api_key`` guards the documentation endpoints. ``get_user_id`` /
``require_user_id`` carry the caller's anonymous identity in the ``X-User-Id``
header instead of the URL query string, keeping ids (and the admin token,
which is just a special user id) out of access logs, proxy logs, and Referer
headers.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, Security
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


async def get_user_id(x_user_id: str | None = Header(default=None)) -> str:
    """Identity for read endpoints. Empty is allowed: an anonymous caller with
    no id simply sees the publicly readable (empty-``user_id``) stories."""
    return (x_user_id or "").strip()


async def require_user_id(x_user_id: str | None = Header(default=None)) -> str:
    """Identity for write/mutating endpoints. Must be present and non-empty so
    a caller cannot act as the public (empty-``user_id``) bucket."""
    user = (x_user_id or "").strip()
    if not user:
        raise HTTPException(status_code=401, detail="Missing user identity")
    return user
