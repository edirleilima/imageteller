"""Story endpoints (thin): upload-to-story, listing, fetch, save, delete, regenerate."""
from __future__ import annotations

import io
import os
import re
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, Query, Form, HTTPException, Request
from PIL import Image

from app.config import paths, urls, uploads, ratelimits
from app.ratelimit import limiter
from app.schemas import Chapter
from app.security import get_user_id, require_user_id
from app.story import service

router = APIRouter()


def validate_file_type(filename: str) -> None:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in uploads.allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type")


def validate_image_content(contents: bytes) -> None:
    """Reject anything that is not a decodable image, regardless of extension."""
    try:
        with Image.open(io.BytesIO(contents)) as img:
            img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image content")


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)


@router.post("/image-to-story/")
@limiter.limit(ratelimits.generate)
async def image_to_story(
    request: Request,
    files: List[UploadFile] = File(...),
    captions: List[str] = Form(...),
    genre: str = Query(...),
    user: str = Depends(require_user_id),
):
    if len(files) > uploads.max_files:
        raise HTTPException(
            status_code=413,
            detail=f"Too many files (max {uploads.max_files} per request)",
        )

    if captions is None:
        captions = [""] * len(files)
    elif len(captions) < len(files):
        captions.extend([""] * (len(files) - len(captions)))

    image_inputs = []
    for index, file in enumerate(files):
        contents = await file.read()
        if len(contents) > uploads.max_file_size:
            raise HTTPException(status_code=413, detail="File too large")
        validate_file_type(file.filename)
        validate_image_content(contents)
        unique_filename = str(uuid.uuid4()) + sanitize_filename(os.path.splitext(file.filename)[-1])
        file_path = os.path.join(paths.images, unique_filename)
        file_url = urls.image_url + unique_filename
        with open(file_path, "wb") as f:
            f.write(contents)
        image_inputs.append({"url": file_url, "path": file_path, "caption": captions[index]})

    return service.compose_story_from_images(image_inputs, genre, user)


@router.post("/get-stories/")
@limiter.limit(ratelimits.read)
async def get_stories(request: Request, user: str = Depends(get_user_id)):
    return service.list_stories(user)


@router.post("/get-story/")
@limiter.limit(ratelimits.read)
async def get_story(
    request: Request, id: str = Query(...), user: str = Depends(get_user_id)
):
    return service.get_story_detail(id, user)


@router.post("/save-story/")
@limiter.limit(ratelimits.write)
async def save_story(
    request: Request, id: str = Query(...), user: str = Depends(require_user_id)
):
    return service.save_story(id, user)


@router.post("/delete-story/")
@limiter.limit(ratelimits.write)
async def delete_story(
    request: Request, id: str = Query(...), user: str = Depends(require_user_id)
):
    return service.delete_story(id, user)


@router.post("/regenerate-chapter/")
@limiter.limit(ratelimits.regenerate)
async def regenerate_chapter(
    request: Request, chapter: Chapter, user: str = Depends(require_user_id)
):
    return service.regenerate_chapter(chapter, user)
