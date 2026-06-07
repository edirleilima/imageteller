"""High-level story operations."""
from __future__ import annotations

import random
import re

import mysql.connector

from app.config import comfyui, llm, paths, urls
from app.database import db_cursor
from app.llm import send_llm_request
from app.characters import (
    update_character_library,
    generate_illustration_description,
    generate_character_tags,
    update_actor_library,
    replace_actors_in_prompt,
    convert_actor_library_to_string,
)
from app.logging_utils import log_error
from app.media import generate_image_description, submit_image_job
from app.schemas import Chapter
from app.story import repository as repo
from app.story.ownership import is_admin
from app.story.prompts import (
    build_story_prompt,
    system_message,
    regenerate_instruction,
)

_ILLUSTRATION_STYLE = (
    "Photography, realistic detailed skin, 4k, highly detailed, diffused soft "
    "lighting, shallow depth of field, sharp focus, hyperrealism, cinematic lighting."
)


# ---- pure generation / parsing -----------------------------------------
def generate_story(image_descriptions, genre: str) -> str:
    prompt = build_story_prompt(image_descriptions, genre, True)
    messages = [{"role": "system", "content": system_message(genre)}]
    messages.append({"role": "user", "content": prompt})
    return send_llm_request(messages, llm.provider, llm.model, llm.temperature)


def regenerate_chapter_for_story(story: dict, chapter_id) -> str:
    prompt = build_story_prompt(story["image_desc"], story["genre"], False)
    messages = [{"role": "system", "content": system_message(story["genre"])}]
    messages.append({"role": "user", "content": prompt})

    story_text = "# " + story["title"] + "\n"
    regenerate_chapter_title = ""
    for chapter in story["chapters"]:
        story_text = story_text + "## " + chapter["title"] + "\n"
        story_text = story_text + "" + chapter["text"] + "\n"
        if str(chapter["id"]) == str(chapter_id):
            regenerate_chapter_title = chapter["title"]

    messages.append({"role": "assistant", "content": story_text})
    messages.append(
        {"role": "user", "content": regenerate_instruction(story["genre"], regenerate_chapter_title)}
    )
    return send_llm_request(messages, llm.provider, llm.model, llm.temperature)


def parse_story(markdown_story: str) -> dict:
    lines = markdown_story.split("\n")
    title = ""
    alignments = ["left", "right", "full"]
    chapters = []
    chapter_title = ""
    chapter_text = ""
    title_regex = re.compile(r"^# (.+)")
    chapter_title_regex = re.compile(r"^## (.+)")
    for line in lines:
        title_match = title_regex.match(line)
        chapter_title_match = chapter_title_regex.match(line)
        if title_match:
            title = title_match.group(1)
        elif chapter_title_match:
            if chapter_title:
                chapters.append({
                    "title": chapter_title.replace("**", ""),
                    "text": chapter_text.strip(),
                    "alignment": random.choice(alignments),
                })
                chapter_text = ""
            chapter_title = chapter_title_match.group(1)
        else:
            chapter_text += line + "\n"
    if chapter_title:
        chapters.append({
            "title": chapter_title.replace("**", ""),
            "text": chapter_text.strip(),
            "alignment": random.choice(alignments),
        })
    return {"title": title.replace("**", ""), "chapters": chapters}


# ---- persistence (swallow DB errors, return the story dict) -------------
def save_generated_story(parsed_story: dict, user_id: str, genre: str, image_desc) -> dict:
    image_desc_str = ""
    for i in range(0, len(image_desc)):
        image_desc_str = image_desc_str + str(i) + ". " + image_desc[i] + "\n"
    try:
        with db_cursor() as cursor:
            story_id = repo.insert_story(cursor, parsed_story["title"], genre, image_desc_str, user_id)
            parsed_story["id"] = story_id
            for chapter in parsed_story["chapters"]:
                chapter["id"] = repo.insert_chapter(
                    cursor, story_id, chapter["title"], chapter["text"], chapter["alignment"]
                )
    except mysql.connector.Error as err:
        log_error(f"save_generated_story failed: {err}")
    return parsed_story


def update_story_after_regeneration(parsed_story: dict, story_id, chapter_id) -> dict:
    try:
        with db_cursor() as cursor:
            repo.mark_chapters_deleted_from(cursor, story_id, chapter_id)
            parsed_story["id"] = story_id
            for chapter in parsed_story["chapters"]:
                old_chapter = repo.find_active_chapter_by_title(cursor, story_id, chapter["title"])
                if old_chapter:
                    chapter["id"] = old_chapter[0]
                    chapter["title"] = old_chapter[2]
                    chapter["text"] = old_chapter[3]
                    chapter["alignment"] = old_chapter[4]
                else:
                    chapter["id"] = repo.insert_chapter(
                        cursor, story_id, chapter["title"], chapter["text"], chapter["alignment"]
                    )
    except mysql.connector.Error as err:
        log_error(f"update_story_after_regeneration failed: {err}")
    return parsed_story


# ---- request-level orchestration ---------------------------------------
def compose_story_from_images(image_inputs: list[dict], genre: str, user: str) -> dict:
    """``image_inputs``: list of ``{"url", "path", "caption"}`` for saved uploads."""
    descriptions = []
    for item in image_inputs:
        desc = generate_image_description(item["url"], item["path"], item["caption"])
        descriptions.append(desc)
    story_markdown = generate_story(descriptions, genre)
    story = parse_story(story_markdown)
    return save_generated_story(story, user, genre, descriptions)


def list_stories(user: str) -> list[dict]:
    try:
        with db_cursor() as cursor:
            stories = repo.list_all_stories(cursor) if is_admin(user) else repo.list_user_stories(cursor, user)
            all_stories = []
            for story in stories:
                candelete = 1
                if (story[2] == "") or is_admin(user):
                    candelete = 0
                all_stories.append(
                    {"id": story[0], "title": story[1], "date": story[5], "can_delete": candelete}
                )
            return all_stories
    except mysql.connector.Error as err:
        log_error(f"list_stories failed: {err}")
        return []


def get_story_detail(story_id: str, user: str) -> dict:
    try:
        with db_cursor() as cursor:
            story = (
                repo.get_story_by_id_admin(cursor, story_id)
                if is_admin(user)
                else repo.get_story_for_user(cursor, story_id, user)
            )
            if story:
                story_data = {"id": story[0], "title": story[1]}
                chapters = repo.get_active_chapters(cursor, story_id)
                story_data["chapters"] = [
                    {"id": c[0], "title": c[2], "text": c[3], "alignment": c[4]} for c in chapters
                ]
                return story_data
            else:
                return {}
    except mysql.connector.Error as err:
        log_error(f"get_story_detail failed: {err}")
        return {}


def save_story(story_id: str, user: str) -> dict:
    try:
        with db_cursor() as cursor:
            story = repo.get_draft_story_owned(cursor, story_id, user)
            if story:
                repo.mark_story_saved(cursor, story_id, user)
                return {"status": "success"}
    except mysql.connector.Error as err:
        log_error(f"save_story failed: {err}")
        return {"status": "failure"}
    return {"status": "failure"}


def delete_story(story_id: str, user: str) -> dict:
    try:
        with db_cursor() as cursor:
            story = repo.get_active_story_owned(cursor, story_id, user)
            if story:
                repo.mark_story_deleted(cursor, story_id, user)
                return {"status": "success"}
    except mysql.connector.Error as err:
        log_error(f"delete_story failed: {err}")
        return {"status": "failure"}
    return {"status": "failure"}


async def illustrate_chapter(chapter: Chapter, user: str) -> dict:
    chapter_url = urls.chapter_url + str(chapter.story_id) + "/" + str(chapter.chapter_id)
    improved_prompt = ""
    try:
        with db_cursor() as cursor:
            story = repo.get_draft_story_owned(cursor, chapter.story_id, user)
            if not story:
                # No owned draft: return the URL without generating (matches original).
                return {"url": chapter_url}
            character_library = story[7] if story[7] else ""
            actor_library_str = story[8] if story[8] else ""
            character_library = update_character_library(chapter.text, character_library)
            prompt = generate_illustration_description(chapter.text, character_library)
            prompt = generate_character_tags(prompt, character_library)
            actor_library = update_actor_library(actor_library_str, prompt)
            improved_prompt = replace_actors_in_prompt(actor_library, prompt)
            actor_library_str = convert_actor_library_to_string(actor_library)
            repo.update_story_libraries(
                cursor, chapter.story_id, user, character_library, actor_library_str
            )
        # db_cursor committed on clean exit; generate the image afterwards.
    except mysql.connector.Error as err:
        log_error(f"illustrate_chapter failed: {err}")
        return {}

    imgfilename = str(chapter.story_id) + "_" + str(chapter.chapter_id) + ".png"
    imgfullpath = paths.chapters + imgfilename
    params = (
        comfyui.workflow_path,
        improved_prompt + " " + _ILLUSTRATION_STYLE,
        comfyui.negative_prompt,
        -1,
        imgfullpath,
    )
    await submit_image_job(params)
    return {"url": chapter_url}


def regenerate_chapter(chapter: Chapter, user: str) -> dict:
    try:
        with db_cursor() as cursor:
            story = repo.get_draft_story_owned(cursor, chapter.story_id, user)
            if not story:
                return {"status": "failure"}
            story_data = {
                "id": story[0],
                "title": story[1],
                "genre": story[3],
                "image_desc": story[4],
            }
            chapters = repo.get_active_chapters(cursor, chapter.story_id)
            story_data["chapters"] = [
                {"id": c[0], "title": c[2], "text": c[3], "alignment": c[4]} for c in chapters
            ]
    except mysql.connector.Error as err:
        log_error(f"regenerate_chapter failed: {err}")
        return {"status": "failure"}

    new_story_markdown = regenerate_chapter_for_story(story_data, chapter.chapter_id)
    new_story_parsed = parse_story(new_story_markdown)
    new_story_saved = update_story_after_regeneration(
        new_story_parsed, chapter.story_id, chapter.chapter_id
    )
    return {"status": "success", "story": new_story_saved}
