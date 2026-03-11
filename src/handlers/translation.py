"""Translation command handlers."""

import asyncio
import logging
from typing import Any

from pyrogram import Client
from pyrogram.enums import ParseMode

from ..config import load_config
from ..language import detect_swap_target, is_same_language
from ..translation import EMOJI_PATTERN, translate_text_with_fallback
from ..utils import create_tracked_task, delete_later

logger = logging.getLogger("translate_bot")


async def do_translate_and_edit(
    message: Any,
    original_text: str,
    target_langs_str: str,
    mode: str = "append",
    skip_if_target: bool = False,
) -> None:
    config = load_config()
    current_engine = config.get("engine", "gemini")
    target_langs = [lang.strip() for lang in target_langs_str.split(",") if lang.strip()]

    if skip_if_target and len(target_langs) == 1:
        if is_same_language(original_text, target_langs[0]):
            return

    text_stripped = original_text.strip()
    if text_stripped and text_stripped.isdigit():
        return

    if text_stripped and all(c in "0123456789.,!?@#$%^&*()+-=/<>'\"[]{}:;|~` \n\t" for c in text_stripped):
        return

    if text_stripped and EMOJI_PATTERN.sub("", text_stripped).strip() == "":
        return

    try:
        loading = f"<blockquote>⏳ 翻译中 ({current_engine.upper()})...</blockquote>"
        await message.edit_text(
            f"{original_text}\n{loading}" if mode == "append" else loading,
            parse_mode=ParseMode.HTML,
        )
        results = await asyncio.gather(
            *[translate_text_with_fallback(original_text, lang, current_engine) for lang in target_langs]
        )
        final_blocks: list[str] = []
        has_error = False
        for lang, result in zip(target_langs, results):
            if result.startswith("ERROR:"):
                has_error = True
                final_blocks.append(f"<blockquote>❌ [{lang.upper()}] 翻译失败</blockquote>")
            else:
                prefix = f"<b>[{lang.upper()}]</b> " if len(target_langs) > 1 else ""
                final_blocks.append(f"<blockquote>{prefix}{result}</blockquote>")
        final_text = (
            f"{original_text}\n" + "\n".join(final_blocks)
            if mode == "append" else "\n\n".join(final_blocks)
        )
        await message.edit_text(final_text, parse_mode=ParseMode.HTML)
        if has_error:
            await asyncio.sleep(5)
            await message.edit_text(original_text)
    except Exception as e:
        logger.exception("do_translate_and_edit failed")
        await message.edit_text(f"{original_text}\n\n⚠️ 系统异常: {str(e)[:50]}")
        create_tracked_task(delete_later(message, 5))


async def translate_reply_cmd(client: Client, message: Any) -> None:
    config = load_config()
    if message.reply_to_message and message.reply_to_message.text:
        await do_translate_and_edit(
            message, message.reply_to_message.text,
            config.get("home_lang", "zh-CN"), mode="replace"
        )


async def tr_cmd(client: Client, message: Any) -> None:
    config = load_config()
    await do_translate_and_edit(message, message.matches[0].group(1), config["default_lang"], mode="append")


async def t_cmd(client: Client, message: Any) -> None:
    await do_translate_and_edit(message, message.matches[0].group(2), message.matches[0].group(1), mode="append")


async def rr_cmd(client: Client, message: Any) -> None:
    config = load_config()
    await do_translate_and_edit(message, message.matches[0].group(1), config["default_lang"], mode="replace")


async def r_cmd(client: Client, message: Any) -> None:
    await do_translate_and_edit(message, message.matches[0].group(2), message.matches[0].group(1), mode="replace")


async def auto_translate_handler(client: Client, message: Any) -> None:
    config = load_config()
    auto = config.get("auto_cmd", "")
    if not auto:
        return
    text = message.text
    parts = auto.split(" ", 1)
    cmd = parts[0]

    if cmd == "swap":
        target_lang = detect_swap_target(
            text, config.get("home_lang", "zh-CN"), config.get("default_lang", "ja")
        )
        await do_translate_and_edit(message, text, target_lang, mode="append")
    elif cmd == "tr":
        await do_translate_and_edit(message, text, config["default_lang"], mode="append", skip_if_target=True)
    elif cmd == "rr":
        await do_translate_and_edit(message, text, config["default_lang"], mode="replace", skip_if_target=True)
    elif cmd == "t" and len(parts) > 1:
        await do_translate_and_edit(message, text, parts[1], mode="append", skip_if_target=True)
    elif cmd == "r" and len(parts) > 1:
        await do_translate_and_edit(message, text, parts[1], mode="replace", skip_if_target=True)
