"""Image endpoints: chapter illustration + serving generated image files."""
from __future__ import annotations

import mimetypes
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import paths
from app.schemas import Chapter
from app.story import service

router = APIRouter()


@router.post("/illustrate-chapter/")
async def illustrate_chapter(chapter: Chapter):
    return await service.illustrate_chapter(chapter)


@router.api_route("/images/{image_name}", methods=["GET", "HEAD"])
async def get_image(image_name: str):
    safe_name = os.path.basename(image_name)
    image_path = os.path.join(paths.images, safe_name)
    if not os.path.isfile(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    mime_type, _ = mimetypes.guess_type(image_path)
    return FileResponse(image_path, media_type=mime_type)


@router.api_route("/chapters/{story_id}/{chapter_id}", methods=["GET", "HEAD"])
async def get_chapter_image(story_id: int, chapter_id: int):
    image_path = os.path.join(paths.chapters, str(story_id) + "_" + str(chapter_id) + ".png")
    if not os.path.isfile(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    mime_type, _ = mimetypes.guess_type(image_path)
    return FileResponse(image_path, media_type=mime_type)
