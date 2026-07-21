"""Data access for stories and chapters."""
from __future__ import annotations

from typing import Any

Cursor = Any
Row = tuple


# ---- stories ------------------------------------------------------------
def insert_story(
    cursor: Cursor, title: str, genre: str, image_desc: str, user_id: str
) -> int:
    cursor.execute(
        "INSERT INTO story (title, genre, image_desc, user_id, deleted) VALUES (%s, %s, %s, %s, 2)",
        (title, genre, image_desc, user_id),
    )
    return cursor.lastrowid


def get_draft_story_owned(cursor: Cursor, story_id, user_id) -> Row | None:
    cursor.execute(
        "SELECT * FROM story WHERE id = %s AND user_id = %s AND deleted = 2",
        (story_id, user_id),
    )
    return cursor.fetchone()


def get_active_story_owned(cursor: Cursor, story_id, user_id) -> Row | None:
    cursor.execute(
        "SELECT * FROM story WHERE id = %s AND user_id = %s AND deleted = 0",
        (story_id, user_id),
    )
    return cursor.fetchone()


def get_story_by_id_admin(cursor: Cursor, story_id) -> Row | None:
    cursor.execute("SELECT * FROM story WHERE id = %s", (story_id,))
    return cursor.fetchone()


def get_story_for_user(cursor: Cursor, story_id, user_id) -> Row | None:
    cursor.execute(
        "SELECT * FROM story WHERE id = %s AND (user_id = %s OR user_id = '') AND deleted = 0",
        (story_id, user_id),
    )
    return cursor.fetchone()


def list_all_stories(cursor: Cursor) -> list[Row]:
    cursor.execute("SELECT * FROM story WHERE TRIM(title) <> ''")
    return cursor.fetchall()


def list_user_stories(cursor: Cursor, user_id) -> list[Row]:
    cursor.execute(
        "SELECT * FROM story WHERE (user_id = %s OR user_id = '') AND deleted = 0 AND TRIM(title) <> ''",
        (user_id,),
    )
    return cursor.fetchall()


def update_story_libraries(
    cursor: Cursor, story_id, user_id, characters: str, actors: str
) -> None:
    cursor.execute(
        "UPDATE story SET characters = %s, actors = %s WHERE id = %s AND user_id = %s",
        (characters, actors, story_id, user_id),
    )


def mark_story_saved(cursor: Cursor, story_id, user_id) -> None:
    cursor.execute(
        "UPDATE story SET deleted = 0 WHERE id = %s AND user_id = %s",
        (story_id, user_id),
    )


def mark_story_deleted(cursor: Cursor, story_id, user_id) -> None:
    cursor.execute(
        "UPDATE story SET deleted = 1 WHERE id = %s AND user_id = %s",
        (story_id, user_id),
    )


# ---- chapters -----------------------------------------------------------
def insert_chapter(
    cursor: Cursor, story_id, title: str, text: str, alignment: str
) -> int:
    cursor.execute(
        "INSERT INTO chapter (story_id, title, text, alignment) VALUES (%s, %s, %s, %s)",
        (story_id, title, text, alignment),
    )
    return cursor.lastrowid


def get_active_chapters(cursor: Cursor, story_id) -> list[Row]:
    cursor.execute(
        "SELECT * FROM chapter WHERE story_id = %s AND deleted = 0",
        (story_id,),
    )
    return cursor.fetchall()


def mark_chapters_deleted_from(cursor: Cursor, story_id, chapter_id) -> None:
    cursor.execute(
        "UPDATE chapter SET deleted = 1 WHERE story_id = %s AND id >= %s",
        (story_id, chapter_id),
    )


def find_active_chapter_by_title(cursor: Cursor, story_id, title: str) -> Row | None:
    cursor.execute(
        "SELECT * FROM chapter WHERE story_id = %s AND title = %s AND deleted = 0",
        (story_id, title),
    )
    return cursor.fetchone()
