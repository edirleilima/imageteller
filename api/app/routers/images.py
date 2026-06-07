"""Image endpoints: chapter illustration + serving generated image files."""
from __future__ import annotations

import mimetypes
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from app.config import paths, ratelimits
from app.ratelimit import limiter
from app.schemas import Chapter
from app.security import require_user_id
from app.story import service

router = APIRouter()

# Returned on every served media file so browsers never MIME-sniff an uploaded
# file into an executable type.
_NOSNIFF = {"X-Content-Type-Options": "nosniff"}


@router.post("/illustrate-chapter/")
@limiter.limit(ratelimits.illustrate)
async def illustrate_chapter(
    request: Request, chapter: Chapter, user: str = Depends(require_user_id)
):
    return await service.illustrate_chapter(chapter, user)


@router.api_route("/images/{image_name}", methods=["GET", "HEAD"])
@limiter.limit(ratelimits.media)
async def get_image(request: Request, image_name: str):
    safe_name = os.path.basename(image_name)
    image_path = os.path.join(paths.images, safe_name)
    if not os.path.isfile(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    mime_type, _ = mimetypes.guess_type(image_path)
    return FileResponse(
        image_path, media_type=mime_type or "application/octet-stream", headers=_NOSNIFF
    )


@router.api_route("/chapters/{story_id}/{chapter_id}", methods=["GET", "HEAD"])
@limiter.limit(ratelimits.media)
async def get_chapter_image(request: Request, story_id: int, chapter_id: int):
    image_path = os.path.join(paths.chapters, str(story_id) + "_" + str(chapter_id) + ".png")
    if not os.path.isfile(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    mime_type, _ = mimetypes.guess_type(image_path)
    return FileResponse(
        image_path, media_type=mime_type or "application/octet-stream", headers=_NOSNIFF
    )
