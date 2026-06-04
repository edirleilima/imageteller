"""Story-generation domain logic."""
from app.story.service import (
    generate_story,
    regenerate_chapter_for_story,
    parse_story,
    save_generated_story,
    update_story_after_regeneration,
    compose_story_from_images,
    list_stories,
    get_story_detail,
    save_story,
    delete_story,
    illustrate_chapter,
    regenerate_chapter,
)
from app.story.ownership import is_admin

__all__ = [
    "generate_story",
    "regenerate_chapter_for_story",
    "parse_story",
    "save_generated_story",
    "update_story_after_regeneration",
    "compose_story_from_images",
    "list_stories",
    "get_story_detail",
    "save_story",
    "delete_story",
    "illustrate_chapter",
    "regenerate_chapter",
    "is_admin",
]
