"""Settings & configuration command handlers."""

from typing import Any

from pyrogram import Client
from pyrogram.enums import ParseMode

from ..clients import clear_clients
from ..config import load_config, save_config
from ..utils import create_tracked_task, delete_later


async def setkey_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(maxsplit=2)
    if len(parts) == 3:
        engine, new_key = parts[1].strip().lower(), parts[2].strip()
        config = load_config()
        if engine in ("openai", "gemini"):
            api_keys = config.get("api_keys", {})
            api_keys[engine] = new_key
            clear_clients()
            save_config("api_keys", api_keys)
            await message.edit_text(f"✅ `{engine}` 的 API Key 已更新！", parse_mode=ParseMode.MARKDOWN)
        else:
            await message.edit_text("❌ 只能修改 `openai` 或 `gemini` 的 Key。")
    else:
        await message.edit_text("❌ 用法: `.setkey <openai/gemini> <KEY>`")
    create_tracked_task(delete_later(message))


async def auto_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(" ", 1)
    if len(parts) == 1 or parts[1].strip().lower() in ("off", "stop"):
        save_config("auto_cmd", "")
        await message.edit_text("🛑 自动模式已关闭")
    else:
        save_config("auto_cmd", parts[1].strip())
        await message.edit_text(f"✅ 自动模式已设为: `.{parts[1].strip()}`")
    create_tracked_task(delete_later(message))


async def setengine_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(" ", 1)
    if len(parts) > 1:
        save_config("engine", parts[1].strip().lower())
        await message.edit_text(f"🚀 引擎切换至: **{parts[1].strip()}**", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.edit_text("❌ 用法: `.setengine <名称>`")
    create_tracked_task(delete_later(message))


async def setmodel_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(" ", 1)
    if len(parts) > 1:
        config = load_config()
        engine = config.get("engine", "gemini")
        new_model = parts[1].strip()
        if engine in ("openai", "gemini"):
            m = config.get("models", {})
            m[engine] = new_model
            save_config("models", m)
        elif engine in config.get("custom_engines", {}):
            config["custom_engines"][engine]["model"] = new_model
            save_config("custom_engines", config["custom_engines"])
        await message.edit_text(f"✅ `{engine}` 模型改为: **{new_model}**", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.edit_text("❌ 用法: `.setmodel <模型名>`")
    create_tracked_task(delete_later(message))


async def setlang_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(" ", 1)
    if len(parts) > 1:
        save_config("default_lang", parts[1].strip())
        await message.edit_text(f"✅ 默认外语切换为: **{parts[1].strip()}**", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.edit_text("❌ 用法: `.setlang <代码>`")
    create_tracked_task(delete_later(message))


async def sethome_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(" ", 1)
    if len(parts) > 1:
        save_config("home_lang", parts[1].strip())
        await message.edit_text(
            f"✅ 母语设置为: **{parts[1].strip()}**\nSwap 模式将以此判断翻译方向。",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await message.edit_text("❌ 用法: `.sethome zh-CN`")
    create_tracked_task(delete_later(message))


async def _upsert_api(client: Client, message: Any, verb: str) -> None:
    """Shared logic for addapi / editapi."""
    parts = message.text.split(maxsplit=4)
    if len(parts) == 5:
        _, name, url, key, model = parts
        config = load_config()
        config["custom_engines"][name.lower()] = {"base_url": url, "api_key": key, "model": model}
        save_config("custom_engines", config["custom_engines"])
        await message.edit_text(f"✅ {verb}引擎: `{name}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.edit_text("❌ 用法: `.addapi <名称> <base_url> <api_key> <model>`")
    create_tracked_task(delete_later(message))


async def addapi_cmd(client: Client, message: Any) -> None:
    await _upsert_api(client, message, "添加")


async def editapi_cmd(client: Client, message: Any) -> None:
    await _upsert_api(client, message, "修改")


async def delapi_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(" ", 1)
    if len(parts) > 1:
        name = parts[1].strip().lower()
        config = load_config()
        if name in config["custom_engines"]:
            del config["custom_engines"][name]
            save_config("custom_engines", config["custom_engines"])
            if config.get("engine") == name:
                save_config("engine", "gemini")
            await message.edit_text(f"🗑 删除引擎: `{name}`", parse_mode=ParseMode.MARKDOWN)
        else:
            await message.edit_text(f"❌ 引擎 `{name}` 不存在")
    else:
        await message.edit_text("❌ 用法: `.delapi <名称>`")
    create_tracked_task(delete_later(message))
