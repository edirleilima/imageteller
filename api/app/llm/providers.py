"""Provider-specific request implementations."""
from __future__ import annotations

import time

import openai
from openai import OpenAIError
from ollama import ResponseError

from app.llm.clients import (
    client_openai,
    client_ollama,
    client_ollama_image,
    client_vllm,
)
from app.logging_utils import write_to_log

Message = dict


def send_openai_request(
    messages: list[Message], model_name: str, temperature: float
) -> tuple[bool, str]:
    try:
        response = client_openai.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=4096,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        return True, response.choices[0].message.content.strip()
    except openai.APITimeoutError as e:
        write_to_log(f"OpenAI API request timed out: {e}")
        time.sleep(1)
        return False, ""
    except openai.InternalServerError as e:
        write_to_log(f"OpenAI API returned an API Error: {e}")
        time.sleep(1)
        return False, ""
    except openai.APIConnectionError as e:
        write_to_log(f"OpenAI API request failed to connect: {e}")
        time.sleep(1)
        return False, ""
    except openai.BadRequestError as e:
        write_to_log(f"OpenAI API request was invalid: {e}")
        time.sleep(1)
        return True, ""
    except openai.AuthenticationError as e:
        write_to_log(f"OpenAI API request was not authorized: {e}")
        time.sleep(1)
        return True, ""
    except openai.PermissionDeniedError as e:
        write_to_log(f"OpenAI API request was not permitted: {e}")
        time.sleep(1)
        return True, ""
    except openai.RateLimitError as e:
        write_to_log(f"OpenAI API request exceeded rate limit: {e}")
        time.sleep(1)
        return False, ""
    except openai.ConflictError as e:
        write_to_log(f"OpenAI API service unavailable: {e}")
        time.sleep(1)
        return False, ""
    except openai.NotFoundError as e:
        write_to_log(f"OpenAI API service unavailable: {e}")
        time.sleep(1)
        return False, ""
    except openai.UnprocessableEntityError as e:
        write_to_log(f"OpenAI API service unavailable: {e}")
        time.sleep(1)
        return False, ""


def send_ollama_request(
    messages: list[Message], model_name: str, temperature: float
) -> tuple[bool, str]:
    try:
        response = client_ollama.chat(
            model=model_name,
            messages=messages,
            think=False,
            options={"temperature": temperature},
        )
        return True, response["message"]["content"].strip()
    except ResponseError as e:
        write_to_log(f"Ollama Error: {e.error}")
        return True, ""


def send_ollama_image_request(
    messages: list[Message], model_name: str, temperature: float
) -> tuple[bool, str]:
    """Vision request against the dedicated image Ollama endpoint."""
    try:
        response = client_ollama_image.chat(
            model=model_name,
            messages=messages,
            options={"temperature": temperature},
        )
        return True, response["message"]["content"].strip()
    except ResponseError as e:
        write_to_log(f"Ollama Error: {e.error}")
        return True, ""


def send_vllm_request(
    messages: list[Message], model_name: str, temperature: float
) -> tuple[bool, str]:
    try:
        response = client_vllm.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            extra_body={
                "chat_template_kwargs": {"enable_thinking": False},
                "reasoning_effort": "low",
            },
        )
        return True, (response.choices[0].message.content or "").strip()
    except OpenAIError as e:
        write_to_log(f"vLLM Error: {e}")
        return True, ""
