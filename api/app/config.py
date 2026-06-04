"""Application configuration."""
from __future__ import annotations

import base64
import os
import uuid
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise RuntimeError(f"Required environment variable {name!r} is not set")
    return value


def _float_env(name: str) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        raise RuntimeError(f"Required environment variable {name!r} is not set")
    return float(raw)


@dataclass(frozen=True)
class DataPaths:
    base: str
    images: str
    chapters: str

    @classmethod
    def from_env(cls) -> "DataPaths":
        base = _required("DATA_PATH")
        return cls(base=base, images=f"{base}/images", chapters=f"{base}/chapters/")


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    model: str
    temperature: float
    character_lib_provider: str
    character_lib_model: str
    character_lib_temperature: float
    image_provider: str
    image_model: str
    image_temperature: float
    ollama_server: str
    ollama_server_image: str
    vllm_server: str
    openai_key: str

    @classmethod
    def from_env(cls) -> "LLMSettings":
        return cls(
            provider=_required("LLM_PROVIDER"),
            model=_required("LLM_MODEL"),
            temperature=_float_env("LLM_TEMPERATURE"),
            character_lib_provider=_required("LLM_CHARACTER_LIB_PROVIDER"),
            character_lib_model=_required("LLM_CHARACTER_LIB_MODEL"),
            character_lib_temperature=_float_env("LLM_CHARACTER_LIB_TEMPERATURE"),
            image_provider=_required("LLM_IMAGE_PROVIDER"),
            image_model=_required("LLM_IMAGE_MODEL"),
            image_temperature=_float_env("LLM_IMAGE_TEMPERATURE"),
            ollama_server=_required("OLLAMA_SERVER"),
            ollama_server_image=_required("OLLAMA_SERVER_IMAGE"),
            vllm_server=_required("VLLM_SERVER"),
            openai_key=_required("OPENAI_KEY"),
        )


@dataclass(frozen=True)
class DatabaseSettings:
    user: str
    password: str
    host: str
    database: str

    def as_kwargs(self) -> dict[str, str]:
        return {
            "user": self.user,
            "password": self.password,
            "host": self.host,
            "database": self.database,
        }

    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        return cls(
            user=_required("DB_USER"),
            password=_required("DB_PASSWORD"),
            host=_required("DB_HOST"),
            database=_required("DB_DATABASE"),
        )


@dataclass(frozen=True)
class ComfyUISettings:
    server: str
    username: str
    password: str
    workflow_path: str
    client_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    negative_prompt: str = (
        "((poorly drawn hands)), ((poorly drawn face)), (((deformed))), blurry, "
        "((bad anatomy)), (((bad proportions))), ((extra limbs)), cloned face, "
        "((((ugly)))), (((duplicate))), ((mutilated)), extra fingers, "
        "(too many fingers), mutated hands, (((disfigured))), out of frame, "
        "extra limbs, gross proportions, (malformed limbs), ((missing arms)), "
        "((missing legs)), (((extra arms))), (((extra legs))), (fused fingers), "
        "(((long neck)))"
    )

    @property
    def auth_header(self) -> str:
        token = base64.b64encode(
            f"{self.username}:{self.password}".encode("utf-8")
        ).decode("utf-8")
        return f"Basic {token}"

    @classmethod
    def from_env(cls) -> "ComfyUISettings":
        return cls(
            server=_required("COMFYUI_SERVER"),
            username=_required("COMFYUI_USERNAME"),
            password=_required("COMFYUI_PASSWORD"),
            workflow_path="/code/app/assets/workflows/workflow_flux_schnell_8_api.json",
        )


@dataclass(frozen=True)
class APISettings:
    api_key: str
    api_key_name: str = "access_token"
    root_path: str = "/imageteller-api"
    domain_url: str = ""
    admin_user: str = ""

    @classmethod
    def from_env(cls) -> "APISettings":
        return cls(
            api_key=_required("API_KEY"),
            domain_url=os.getenv("DOMAIN_URL", ""),
            admin_user=_required("ADMIN_USER"),
        )


@dataclass(frozen=True)
class URLSettings:
    image_url: str
    chapter_url: str
    nlp_api_server: str

    @classmethod
    def from_env(cls) -> "URLSettings":
        return cls(
            image_url=_required("IMAGE_URL"),
            chapter_url=_required("CHAPTER_URL"),
            nlp_api_server=_required("NLP_API_SERVER"),
        )


@dataclass(frozen=True)
class UploadSettings:
    max_file_size: int = 25 * 1024 * 1024
    allowed_extensions: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".gif"})


# Singletons — built once at import, immutable thereafter.
paths = DataPaths.from_env()
llm = LLMSettings.from_env()
db = DatabaseSettings.from_env()
comfyui = ComfyUISettings.from_env()
api = APISettings.from_env()
urls = URLSettings.from_env()
uploads = UploadSettings()
