"""Pre-built provider client singletons."""
from __future__ import annotations

from ollama import Client as OllamaClient
from openai import OpenAI

from app.config import llm

client_openai = OpenAI(api_key=llm.openai_key)
client_ollama = OllamaClient(host=llm.ollama_server)
# ImageTeller uses a *separate* Ollama endpoint for vision/image description.
client_ollama_image = OllamaClient(host=llm.ollama_server_image)
client_vllm = OpenAI(base_url=llm.vllm_server, api_key="NONE")
