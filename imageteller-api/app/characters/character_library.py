"""Character library: visual descriptions extracted from story text via the LLM."""
from __future__ import annotations

import re

from app.config import llm
from app.llm import send_llm_request


def update_character_library(text: str, character_library: str) -> str:
    prompt = "Story Text: " + text + " \n\nCharacter Library: " + character_library + "\n\nRead the provided story text and identify the relevant characters mentioned, focusing on those who are named and visually described (e.g., physical appearance, clothing, expressions). For each character, extract and summarize only their visually observable attributes and age group (e.g., infant, child, teenager, adult, senior, elder, ancient). Do not include personality traits, ideological descriptions, or narrative roles. If the text does not provide visual and clothing details for a character, generate the information according to the narrative context. Ensure that the description of all characters includes their visual attributes (all characters must have a hair color, hairstyle, and eye color defined) and clothes details (all characters must have a clothing type and color defined). Use the following format: NAME: DESCRIPTION, where NAME identifies the character's name (followed by a colon), and DESCRIPTION is a concise paragraph summarizing the character's key visually observable details, such as hair color, eye color, age group, clothing type, and clothing type. This should be concise yet comprehensive enough to maintain consistency across scenes. If a character is already in the Character Library but new details are provided, update the existing entry instead of creating a new one. Ensure that each character pair NAME: DESCRIPTION is presented within square brackets: [NAME: DESCRIPTION]. \n\nEnsure that the Character Library does not include characters whose names are defined by generic role descriptors such as 'villager', 'father', 'dragon' or other unnamed individuals.\n\nVery important: you must write only the Character Library without adding commentaries or notes to your response. Write your response in english only."
    messages = [{"role": "system", "content": ""}]
    messages.append({"role": "user", "content": prompt})
    return send_llm_request(
        messages,
        llm.character_lib_provider,
        llm.character_lib_model,
        llm.character_lib_temperature,
    )


def extract_character_names(text: str) -> list[str]:
    pattern = r"\[([^\]]+)\]"
    names = re.findall(pattern, text)
    return names


def generate_illustration_description(chapter: str, character_library: str) -> str:
    prompt = "Story Chapter: " + chapter + "\n\nCharacter Library: " + character_library + "\n\nIdentify a single significant event in the provided story chapter and write a concise description (maximum of 80 words) to be used as input for a Stable Diffusion model to generate an illustration. Focus on the characters' actions, interactions, and the environment. Only include in the description characters who are explicitly mentioned in the story chapter and refer to them by their names in the generated description. \n\nWhen describing the characters, include all details related to their visual attributes (such as age group, hair color, hairstyle, eye color, clothing type, and clothing colors). If any visual or clothing details for a character are missing from both the chapter and the Character Library, create appropriate attributes that are consistent with the story's setting, genre, and tone. Ensure these details are realistic and coherent with the story context. \n\nVery important: you must write only the description without adding formatting elements, commentaries, or notes to your response. Refer to all characters by name. Write your response in english only."
    messages = [{"role": "system", "content": "You are a creative story writer."}]
    messages.append({"role": "user", "content": prompt})
    return send_llm_request(
        messages,
        llm.character_lib_provider,
        llm.character_lib_model,
        llm.character_lib_temperature,
    )
