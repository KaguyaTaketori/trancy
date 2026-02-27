import json
import os
import time
from typing import Any

CONFIG_FILE = "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "default_lang": "ja",
    "home_lang": "zh-CN",
    "engine": "gemini",
    "custom_engines": {},
    "models": {"openai": "gpt-4o-mini", "gemini": "gemini-1.5-flash"},
    "auto_cmd": "",
    "api_keys": {"openai": "", "gemini": ""},
}

_config_cache: dict[str, Any] | None = None
_cache_timestamp: float = 0
_CACHE_TTL: float = 5.0


def load_config() -> dict[str, Any]:
    global _config_cache, _cache_timestamp
    now = time.monotonic()
    if _config_cache is not None and (now - _cache_timestamp) < _CACHE_TTL:
        return _config_cache
    config = {k: v for k, v in DEFAULT_CONFIG.items()}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config.update(saved)
        except (json.JSONDecodeError, OSError) as e:
            from logging import getLogger
            logger = getLogger("translate_bot")
            logger.warning("Could not load config, using defaults: %s", e)
    _config_cache = config
    _cache_timestamp = now
    return config


def save_config(key: str, value: Any) -> None:
    global _config_cache, _cache_timestamp
    config = load_config()
    config[key] = value
    _config_cache = config
    _cache_timestamp = time.monotonic()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except OSError as e:
        from logging import getLogger
        logger = getLogger("translate_bot")
        logger.error("Failed to save config: %s", e)
