"""Story endpoints (thin): upload-to-story, listing, fetch, save, delete, regenerate."""
from __future__ import annotations

import os
import re
import uuid
from typing import List

from fastapi import APIRouter, File, UploadFile, Query, Form, HTTPException

from app.config import paths, urls, uploads
from app.schemas import Chapter
from app.story import service

router = APIRouter()


def validate_file_type(filename: str) -> None:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in uploads.allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type")


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)


@router.post("/image-to-story/")
async def image_to_story(
    files: List[UploadFile] = File(...),
    captions: List[str] = Form(...),
    genre: str = Query(...),
    user: str = Query(...),
):
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
        unique_filename = str(uuid.uuid4()) + sanitize_filename(os.path.splitext(file.filename)[-1])
        file_path = os.path.join(paths.images, unique_filename)
        file_url = urls.image_url + unique_filename
        with open(file_path, "wb") as f:
            f.write(contents)
        image_inputs.append({"url": file_url, "path": file_path, "caption": captions[index]})

    return service.compose_story_from_images(image_inputs, genre, user)


@router.post("/get-stories/")
async def get_stories(user: str = Query(...)):
    return service.list_stories(user)


@router.post("/get-story/")
async def get_story(id: str = Query(...), user: str = Query(...)):
    return service.get_story_detail(id, user)


@router.post("/save-story/")
async def save_story(id: str = Query(...), user: str = Query(...)):
    return service.save_story(id, user)


@router.post("/delete-story/")
async def delete_story(id: str = Query(...), user: str = Query(...)):
    return service.delete_story(id, user)


@router.post("/regenerate-chapter/")
async def regenerate_chapter(chapter: Chapter):
    return service.regenerate_chapter(chapter)
