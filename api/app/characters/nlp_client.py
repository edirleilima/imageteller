"""Thin wrapper around the external NLP API server."""
from __future__ import annotations

import requests

from app.config import urls
from app.logging_utils import write_to_log


def generate_character_tags(text: str, character_library: str) -> str:
    url = urls.nlp_api_server + "/tag-names/"
    payload = {"text": text, "library": character_library}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        output = response.json().get("output")
        return output
    else:
        write_to_log(f"tag-names failed with status code: {response.status_code}")
    return text


def get_gender(name: str, storyevent: str) -> str:
    url = urls.nlp_api_server + "/classify-gender-using-pronouns/"
    payload = {"name": name, "text": storyevent}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        output = response.json().get("output")
        if output:
            if output == "unknown":
                return get_name_gender(name)
            else:
                return output
        else:
            write_to_log("classify-gender-using-pronouns error: no output")
    else:
        write_to_log(
            f"classify-gender-using-pronouns failed with status code: {response.status_code}"
        )
    return ""


def get_name_gender(name: str) -> str:
    url = urls.nlp_api_server + "/classify-gender/"
    payload = {"text": name}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        output = response.json().get("output")
        if output:
            return output
        else:
            write_to_log("classify-gender error: no output")
    else:
        write_to_log(f"classify-gender failed with status code: {response.status_code}")
    return ""
