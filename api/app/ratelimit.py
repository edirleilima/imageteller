"""Shared rate limiter (abuse control for the public API).

Keyed on the real client IP. Because the API runs behind an Apache reverse
proxy, ``request.client.host`` is the proxy's address, so we read the client
from ``X-Forwarded-For`` when present. For this to be trustworthy the proxy
must set/overwrite that header (e.g. Apache ``mod_remoteip`` /
``RemoteIPHeader X-Forwarded-For``); otherwise a client could spoof it to
dodge limits.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import ratelimits


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    return get_remote_address(request)


limiter = Limiter(key_func=client_ip, storage_uri=ratelimits.storage_uri)
