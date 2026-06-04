"""Request/response schemas."""
from __future__ import annotations

from pydantic import BaseModel


class Chapter(BaseModel):
    """Payload for chapter illustration / regeneration requests."""
    story_id: str
    chapter_id: str
    user: str
    text: str
