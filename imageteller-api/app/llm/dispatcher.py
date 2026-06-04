"""Provider-agnostic dispatch."""
from __future__ import annotations

import re

from app.llm.providers import (
    send_openai_request,
    send_ollama_request,
    send_vllm_request,
)

_THINK_PATTERN = re.compile(r"<think>.*?</think>", flags=re.IGNORECASE | re.DOTALL)


def send_llm_request(
    messages: list[dict],
    provider: str,
    model_name: str,
    temperature: float,
) -> str:
    result = ""
    can_continue = False
    numtries = 0
    while not can_continue:
        if provider == "openai":
            can_continue, result = send_openai_request(messages, model_name, temperature)
        elif provider == "ollama":
            can_continue, result = send_ollama_request(messages, model_name, temperature)
        elif provider == "vllm":
            can_continue, result = send_vllm_request(messages, model_name, temperature)
        numtries = numtries + 1
        if numtries > 15:
            break
    return _THINK_PATTERN.sub("", result.strip()).replace("*", "")
