"""Character/actor library management."""
from app.characters.character_library import (
    update_character_library,
    extract_character_names,
    generate_illustration_description,
)
from app.characters.actor_library import (
    parse_character_actor,
    convert_actor_library_to_string,
    update_actor_library,
    replace_actors_in_prompt,
)
from app.characters.nlp_client import (
    generate_character_tags,
    get_gender,
    get_name_gender,
)

__all__ = [
    "update_character_library",
    "extract_character_names",
    "generate_illustration_description",
    "parse_character_actor",
    "convert_actor_library_to_string",
    "update_actor_library",
    "replace_actors_in_prompt",
    "generate_character_tags",
    "get_gender",
    "get_name_gender",
]
