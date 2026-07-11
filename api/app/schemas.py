"""Request/response schemas."""
from __future__ import annotations

from pydantic import BaseModel


class Chapter(BaseModel):
    """Payload for chapter illustration / regeneration requests."""
    story_id: int
    chapter_id: int
    text: str = ""
