"""Async ComfyUI client + a single-worker queue."""
from __future__ import annotations

import asyncio
import io
import json
import random

import aiohttp
import websockets

from app.config import comfyui
from app.logging_utils import write_to_log

# Public queue and worker --------------------------------------------------
image_generation_queue: asyncio.Queue = asyncio.Queue()


async def image_generation_worker() -> None:
    """Process the queue forever, one request at a time."""
    while True:
        future, params = await image_generation_queue.get()
        try:
            result = await comfyui_generate_image_flux_async(*params)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            image_generation_queue.task_done()


# Low-level ComfyUI helpers ------------------------------------------------
async def _queue_prompt(prompt: dict) -> dict:
    payload = {"prompt": prompt, "client_id": comfyui.client_id}
    headers = {"Authorization": comfyui.auth_header}
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://{comfyui.server}/prompt", json=payload, headers=headers
        ) as resp:
            return await resp.json()


async def _get_image(filename: str, subfolder: str, folder_type: str) -> bytes:
    params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    headers = {"Authorization": comfyui.auth_header}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://{comfyui.server}/view", params=params, headers=headers
        ) as resp:
            return await resp.read()


async def _get_history(prompt_id: str) -> dict:
    headers = {"Authorization": comfyui.auth_header}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://{comfyui.server}/history/{prompt_id}", headers=headers
        ) as resp:
            return await resp.json()


async def _get_images_via_ws(ws, prompt: dict, uri: str, headers: dict) -> dict:
    """Submit the prompt and collect output images via the websocket."""
    prompt_id = (await _queue_prompt(prompt))["prompt_id"]
    output_images: dict[str, list[bytes]] = {}

    while True:
        try:
            out = await asyncio.wait_for(ws.recv(), timeout=30)
        except asyncio.TimeoutError:
            write_to_log("WebSocket recv timed out. Reconnecting...")
            await asyncio.sleep(15)
            ws = await websockets.connect(uri, additional_headers=headers)
            prompt_id = (await _queue_prompt(prompt))["prompt_id"]
            continue
        except websockets.exceptions.ConnectionClosedError as e:
            write_to_log(f"WebSocket connection closed unexpectedly: {e}")
            await asyncio.sleep(15)
            ws = await websockets.connect(uri, additional_headers=headers)
            prompt_id = (await _queue_prompt(prompt))["prompt_id"]
            continue
        except Exception as e:
            write_to_log(f"An unexpected error occurred: {e}")
            await asyncio.sleep(15)
            ws = await websockets.connect(uri, additional_headers=headers)
            prompt_id = (await _queue_prompt(prompt))["prompt_id"]
            continue

        if isinstance(out, str):
            message = json.loads(out)
            if message["type"] == "executing":
                data = message["data"]
                if data["node"] is None and data["prompt_id"] == prompt_id:
                    break

    history = (await _get_history(prompt_id))[prompt_id]
    for node_id, node_output in history["outputs"].items():
        if "images" in node_output:
            collected = []
            for image in node_output["images"]:
                image_data = await _get_image(
                    image["filename"], image["subfolder"], image["type"]
                )
                collected.append(image_data)
            output_images[node_id] = collected

    return output_images


async def comfyui_generate_image_flux_async(
    workflow: str,
    prompt: str,
    negative: str,
    seed: int,
    filename: str,
) -> None:
    """Generate one image and write it to ``filename`` (``seed=-1`` -> random)."""
    with open(workflow, "r") as f:
        promptdata = json.load(f)

    if seed == -1:
        seed = random.randint(0, 2**32 - 1)

    promptdata["6"]["inputs"]["text"] = prompt
    promptdata["25"]["inputs"]["noise_seed"] = seed

    uri = f"wss://{comfyui.server}/ws?clientId={comfyui.client_id}"
    headers = {"Authorization": comfyui.auth_header}
    async with websockets.connect(uri, additional_headers=headers) as ws:
        images = await _get_images_via_ws(ws, promptdata, uri, headers)

    if images:
        bytestream = io.BytesIO(images["9"][0])
        with open(filename, "wb") as outfile:
            outfile.write(bytestream.getbuffer())


async def submit_image_job(params: tuple) -> None:
    """Enqueue a generation job and await its completion.

    ``params`` matches ``comfyui_generate_image_flux_async``:
    ``(workflow, prompt, negative_prompt, seed, output_filename)``.
    """
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    await image_generation_queue.put((future, params))
    await future
