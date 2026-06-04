"""Authorization model for story access (ImageTeller's own)."""
from __future__ import annotations

from app.config import api


def is_admin(user: str) -> bool:
    return user == api.admin_user
