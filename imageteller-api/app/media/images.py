"""Image preprocessing and vision-based description."""
from __future__ import annotations

import base64
import io

from PIL import Image

from app.config import llm
from app.llm import send_llm_request, send_ollama_image_request

_DESCRIPTION_INSTRUCTIONS = (
    "Analyze the provided image and write a short description (a single paragraph) "
    "of the subjects present in the image, including their actions and appearance. "
    "Focus on key elements such as the interactions between subjects and any "
    "significant environmental details that contribute to the mood and context of "
    "the scene. Write the description in a single paragraph without headers, bullet "
    "points, or numbered items. "
)


def convert_to_rgb(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "P"):
        return image.convert("RGB")
    return image


def convert_to_jpeg(image: Image.Image, quality: int = 100) -> bytes:
    byte_arr = io.BytesIO()
    image.save(byte_arr, format="JPEG", quality=quality)
    return byte_arr.getvalue()


def is_jpeg(file: str) -> bool:
    return file.lower().endswith((".jpg", ".jpeg"))


def process_image(uploaded_file: str) -> str:
    """Resize to max width 512, ensure JPEG, return base64 (for Ollama vision)."""
    image = Image.open(uploaded_file)
    base_width = 512
    if image.size[0] > base_width:
        wpercent = base_width / float(image.size[0])
        hsize = int(float(image.size[1]) * float(wpercent))
        image = image.resize((base_width, hsize), Image.Resampling.LANCZOS)

    if not is_jpeg(uploaded_file):
        image = convert_to_rgb(image)
        image_bytes = convert_to_jpeg(image)
    else:
        byte_arr = io.BytesIO()
        image.save(byte_arr, format="JPEG")
        image_bytes = byte_arr.getvalue()

    return base64.b64encode(image_bytes).decode("utf-8")


def generate_image_description(image_url: str, file_path: str, caption: str) -> str:
    """Describe an image via the configured vision provider.

    OpenAI receives the image by URL; Ollama receives a resized base64 image.
    """
    caption_instruction = ""
    if caption != "":
        caption_instruction = (
            "When generating the description, take into account that the image has "
            "the following caption: " + caption
        )
    full_instructions = _DESCRIPTION_INSTRUCTIONS + caption_instruction

    if llm.image_provider == "openai":
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": full_instructions},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url, "detail": "high"},
                    },
                ],
            }
        ]
        return send_llm_request(
            messages, llm.image_provider, llm.image_model, llm.image_temperature
        )

    encoded_image = process_image(file_path)
    messages = [
        {
            "role": "user",
            "content": full_instructions,
            "images": [encoded_image],
        }
    ]
    _can_continue, result = send_ollama_image_request(
        messages, llm.image_model, llm.image_temperature
    )
    result = result.replace("\n", " ")
    return result
