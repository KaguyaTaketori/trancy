import asyncio
import logging
import os
from typing import Any

import httpx
from google import genai
from openai import AsyncOpenAI

logger = logging.getLogger("translate_bot")

FALLBACK_OPENAI_KEY: str = os.getenv("FALLBACK_OPENAI_KEY", "")
FALLBACK_GEMINI_KEY: str = os.getenv("FALLBACK_GEMINI_KEY", "")

_openai_clients: dict[str, AsyncOpenAI] = {}
_gemini_clients: dict[str, genai.Client] = {}
_custom_clients: dict[str, AsyncOpenAI] = {}


def _create_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_connections=10),
    )


_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = _create_http_client()
    return _http_client


def get_openai_client(config: dict[str, Any]) -> AsyncOpenAI:
    key = config["api_keys"].get("openai") or FALLBACK_OPENAI_KEY
    if key not in _openai_clients:
        _openai_clients[key] = AsyncOpenAI(
            api_key=key,
            http_client=get_http_client(),
        )
    return _openai_clients[key]


def get_gemini_client(config: dict[str, Any]) -> genai.Client:
    key = config["api_keys"].get("gemini") or FALLBACK_GEMINI_KEY
    if key not in _gemini_clients:
        _gemini_clients[key] = genai.Client(
            api_key=key,
            http_client=get_http_client(),
        )
    return _gemini_clients[key]


def get_custom_client(cfg: dict[str, Any]) -> AsyncOpenAI:
    """Get or create a cached AsyncOpenAI client for a custom engine."""
    cache_key = f"{cfg['base_url']}|{cfg['api_key']}"
    if cache_key not in _custom_clients:
        _custom_clients[cache_key] = AsyncOpenAI(
            api_key=cfg["api_key"],
            base_url=cfg["base_url"],
            timeout=15.0,
            http_client=get_http_client(),
        )
    return _custom_clients[cache_key]


def clear_clients() -> None:
    global _http_client
    _openai_clients.clear()
    _gemini_clients.clear()
    _custom_clients.clear()
    if _http_client is not None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_http_client.aclose())
        except RuntimeError:
            pass
        _http_client = None
