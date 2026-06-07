"""Authorization model for story access (ImageTeller's own)."""
from __future__ import annotations

import hmac

from app.config import api


def is_admin(user: str) -> bool:
    if not user or not api.admin_user:
        return False
    return hmac.compare_digest(user, api.admin_user)
