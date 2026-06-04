"""Actor library: maps character names to actor names for image prompts."""
from __future__ import annotations

import random
import re

from app.characters.character_library import extract_character_names
from app.characters.nlp_client import get_gender

male_actors = [
    "Leonardo DiCaprio",
    "Brad Pitt",
    "Johnny Depp",
    "Robert Downey Jr.",
    "Tom Hanks",
    "George Clooney",
    "Matt Damon",
    "Ryan Gosling",
    "Chris Hemsworth",
    "Tom Hardy",
    "Idris Elba",
    "Chadwick Boseman",
    "Joseph Gordon-Levitt",
    "Colin Firth",
    "Matthew McConaughey",
]

female_actors = [
    "Scarlett Johansson",
    "Anne Hathaway",
    "Natalie Portman",
    "Emma Stone",
    "Amy Adams",
    "Emma Watson",
    "Rachel McAdams",
    "Jennifer Lawrence",
    "Angelina Jolie",
    "Sandra Bullock",
]

_TITLES_LOWER = [
    "dr", "mrs", "mr", "miss", "ms", "sir", "lady", "lord",
    "prof", "captain", "detective", "inspector",
]


def parse_character_actor(input_string: str) -> dict:
    character_actor_dict = {}
    pairs = input_string.split(";")
    for pair in pairs:
        if pair.strip():
            character, actor = pair.split(":")
            character_actor_dict[character.strip()] = actor.strip()
    return character_actor_dict


def convert_actor_library_to_string(library: dict) -> str:
    pairs = [f"{character}:{actor}" for character, actor in library.items()]
    result_string = "; \n".join(pairs) + "; \n"
    return result_string


def get_random_actor(library: dict, gender: str, males: list, females: list) -> str:
    actor_list = males if gender == "male" else females
    random_actor = random.choice(actor_list)
    while random_actor in library.values():
        random_actor = random.choice(actor_list)
    return random_actor


def normalize_actor_library(library: dict) -> dict:
    normalized_library = {}
    for full_name, actor in library.items():
        name_parts = full_name.split()
        first_name = name_parts[0]
        normalized_library[full_name] = actor
        if first_name.lower() not in _TITLES_LOWER:
            if first_name not in normalized_library:
                normalized_library[first_name] = actor
        if len(name_parts) > 1:
            last_name = name_parts[-1]
            if last_name.isalpha() and last_name not in normalized_library:
                normalized_library[last_name] = actor
    return normalized_library


def remove_titles(name: str) -> str:
    titles = [
        r"Dr\.", r"Mrs\.", r"Mr\.", "Miss", r"Ms\.", "Sir", "Lady", "Lord",
        r"Prof\.", "Captain", "Detective", "Inspector",
    ]
    pattern = r"^(?:" + "|".join(titles) + r")\s*"
    cleaned_name = re.sub(pattern, "", name, flags=re.IGNORECASE).strip()
    return cleaned_name


def update_actor_library(actor_library: str, image_prompt: str) -> dict:
    library = parse_character_actor(actor_library)
    character_names = extract_character_names(image_prompt)
    for name in character_names:
        cleaned_name = remove_titles(name)
        if cleaned_name in library:
            continue
        gender = get_gender(cleaned_name.split()[0], image_prompt)
        actor = get_random_actor(library, gender, male_actors, female_actors)
        library[cleaned_name] = actor
        normalized_names = normalize_actor_library({cleaned_name: actor})
        library.update(normalized_names)
    return library


def replace_actors_in_prompt(actor_library: dict, image_prompt: str) -> str:
    def replace_name(match):
        character_name = match.group(1)
        cleaned_name = remove_titles(character_name)
        actor_name = actor_library.get(cleaned_name, cleaned_name)
        return f"({actor_name}:1.2)"

    return re.sub(r"\[([^\]]+)\]", replace_name, image_prompt)
