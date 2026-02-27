import asyncio
import time
from typing import Any

from pyrogram import Client
from pyrogram.enums import ParseMode

from .clients import clear_clients
from src.config import load_config, save_config
from .language import detect_language, detect_swap_target, is_same_language
from .translation import _translate_with_engine, translate_text_with_fallback
from .utils import create_tracked_task, delete_later


async def do_translate_and_edit(
    message: Any,
    original_text: str,
    target_langs_str: str,
    mode: str = "append",
    skip_if_target: bool = False,
) -> None:
    config = load_config()
    current_engine = config.get("engine", "gemini")
    target_langs = [l.strip() for l in target_langs_str.split(",") if l.strip()]

    if skip_if_target and len(target_langs) == 1:
        if is_same_language(original_text, target_langs[0]):
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
        import logging
        logging.exception("do_translate_and_edit failed")
        await message.edit_text(f"{original_text}\n\n⚠️ 系统异常: {str(e)[:50]}")
        create_tracked_task(delete_later(message, 5))


HELP_TEXT = """\
🤖 **高可用多语翻译网关 · 完整指令手册**
⚙️ 引擎: `{engine}` · 模型: `{model_display}`
🌐 母语: `{home_lang}` · 默认外语: `{default_lang}`
🔄 自动模式: {auto_status}
🔌 自定义引擎: `{custom_list}`

━━━━━━━━━━━━━━━━━━━━━━━
📝 **基础翻译 · 追加模式**
翻译结果追加在原文下方

`.tr <文本>` — 翻译为默认外语
  例: `.tr 今天天气真好`

`.t <语言> <文本>` — 翻译为指定语言
  例: `.t en 你好世界`
  例: `.t ja,ko,en 你好` ← 同时译多语

━━━━━━━━━━━━━━━━━━━━━━━
🔄 **基础翻译 · 替换模式**
原文被翻译结果完全替换

`.rr <文本>` — 替换为默认外语
  例: `.rr 今天天气真好`

`.r <语言> <文本>` — 替换为指定语言
  例: `.r ja 我喜欢猫`

━━━━━━━━━━━━━━━━━━━━━━━
💬 **翻译他人消息**

`.tl` — 翻译你正在回复的消息（译为母语）
  先回复一条消息，再发 `.tl`

━━━━━━━━━━━━━━━━━━━━━━━
🤖 **自动模式**
开启后，每条发出的消息自动处理。
tr/rr 模式内置智能跳过：如果消息已是目标
语言，则自动跳过，不做任何修改。

`.auto swap` — 🌟 **智能双向互译** (最推荐)
  发中文 → 自动追加外语翻译
  发日文/英文等 → 自动追加中文翻译

`.auto tr` — 追加默认外语 (已是目标语则跳过)
`.auto rr` — 替换为默认外语 (已是目标语则跳过)
`.auto t ja` — 追加日语 (已是日语则跳过)
`.auto r ko` — 替换为韩语
`.auto off` — 🛑 关闭自动模式

━━━━━━━━━━━━━━━━━━━━━━━
🔍 **检测与诊断**

`.detect` — 准确识别语言
  例: `.detect 多分風` → `ja` ✅
  或: 回复消息后发 `.detect`

`.ping` — 测试所有引擎延迟
`.status` — 查看所有当前配置

━━━━━━━━━━━━━━━━━━━━━━━
📋 **消息工具**

`.copy` — 复制回复消息的原文
  先回复一条消息，再发 `.copy`

`.len` — 统计字数/字符数
  例: `.len 你好世界` 或回复后发 `.len`

━━━━━━━━━━━━━━━━━━━━━━━
⚙️ **系统配置**

`.setlang <代码>` — 设置默认外语
  例: `.setlang ko` / `.setlang en`

`.sethome <代码>` — 设置母语 (swap判断用)
  例: `.sethome zh-CN`

`.setengine <名称>` — 切换引擎
  可选: `gemini` / `openai` / `google` / 自定义

`.setmodel <模型名>` — 修改当前引擎模型
  例: `.setmodel gpt-4o`

`.setkey <openai/gemini> <KEY>` — 更新 API Key

━━━━━━━━━━━━━━━━━━━━━━━
🔌 **自定义引擎 (兼容 OpenAI API 格式)**

`.addapi <名> <URL> <Key> <模型>` — 添加
  例: `.addapi grok https://api.x.ai/v1 xai-xxx grok-3`

`.editapi <名> <URL> <Key> <模型>` — 修改
`.delapi <名>` — 删除

━
"""


async def help_cmd(client: Client, message: Any) -> None:
    config = load_config()
    engine = config.get("engine", "gemini")
    home_lang = config.get("home_lang", "zh-CN")
    default_lang = config.get("default_lang", "ja")
    model_display = (
        config.get("models", {}).get(engine, "默认")
        if engine in ("openai", "gemini")
        else config.get("custom_engines", {}).get(engine, {}).get("model", "未知")
    )
    auto = config.get("auto_cmd", "")
    auto_status = f"✅ `.{auto}`" if auto else "❌ 关闭"
    custom_list = ", ".join(config.get("custom_engines", {}).keys()) or "无"

    help_text = HELP_TEXT.format(
        engine=engine,
        model_display=model_display,
        home_lang=home_lang,
        default_lang=default_lang,
        auto_status=auto_status,
        custom_list=custom_list,
    )
    await message.edit_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def status_cmd(client: Client, message: Any) -> None:
    config = load_config()
    engine = config.get("engine", "gemini")
    models = config.get("models", {})
    custom_engines = config.get("custom_engines", {})
    api_keys = config.get("api_keys", {})

    def key_status(k: str) -> str:
        return "✅ 已设置" if k else "⚠️ 未设置 (使用内置备用)"

    custom_lines = "\n".join(
        f"  • `{n}` — {c.get('model','?')}  ({c.get('base_url','?')[:40]})"
        for n, c in custom_engines.items()
    ) or "  (无)"

    await message.edit_text(
        "📊 **当前系统状态**\n\n"
        f"🔄 **引擎**: `{engine}`\n"
        f"🧠 **OpenAI 模型**: `{models.get('openai','未设置')}`\n"
        f"🧠 **Gemini 模型**: `{models.get('gemini','未设置')}`\n\n"
        f"🌐 **母语**: `{config.get('home_lang','zh-CN')}`\n"
        f"🌐 **默认外语**: `{config.get('default_lang','ja')}`\n\n"
        f"🤖 **自动模式**: `{'.' + config.get('auto_cmd','') if config.get('auto_cmd') else '关闭'}`\n\n"
        f"🔑 **OpenAI Key**: {key_status(api_keys.get('openai',''))}\n"
        f"🔑 **Gemini Key**: {key_status(api_keys.get('gemini',''))}\n\n"
        f"🔌 **自定义引擎**:\n{custom_lines}",
        parse_mode=ParseMode.MARKDOWN,
    )
    create_tracked_task(delete_later(message, 15))


async def ping_cmd(client: Client, message: Any) -> None:
    config = load_config()
    await message.edit_text("🔍 正在测试所有引擎连接...")
    all_engines = ["gemini", "openai", "google"] + list(config.get("custom_engines", {}).keys())
    lines: list[str] = []
    for engine in all_engines:
        start = time.monotonic()
        try:
            result = await _translate_with_engine("Hello", "zh-CN", engine, config)
            ms = int((time.monotonic() - start) * 1000)
            lines.append(f"✅ `{engine}` — {ms}ms  (`{result[:12]}`)")
        except Exception as e:
            ms = int((time.monotonic() - start) * 1000)
            lines.append(f"❌ `{engine}` — {ms}ms  ({str(e)[:35]})")
    await message.edit_text(
        "📡 **引擎连接测试结果**\n\n" + "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
    )
    create_tracked_task(delete_later(message, 20))


async def detect_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(maxsplit=1)
    target: str | None = (
        parts[1].strip() if len(parts) > 1
        else (message.reply_to_message.text if message.reply_to_message and message.reply_to_message.text else None)
    )
    if not target:
        await message.edit_text(
            "❌ 用法: `.detect <文本>` 或回复消息后发 `.detect`",
            parse_mode=ParseMode.MARKDOWN,
        )
        create_tracked_task(delete_later(message, 5))
        return
    detected = await asyncio.to_thread(detect_language, target)
    preview = target[:40] + ("..." if len(target) > 40 else "")
    await message.edit_text(
        f"🔍 **语言检测结果**\n\n文本: `{preview}`\n检测语言: **`{detected}`**",
        parse_mode=ParseMode.MARKDOWN,
    )
    create_tracked_task(delete_later(message, 8))


async def copy_cmd(client: Client, message: Any) -> None:
    if message.reply_to_message and message.reply_to_message.text:
        await message.edit_text(message.reply_to_message.text)
    else:
        await message.edit_text("❌ 请先回复一条文本消息，再使用 `.copy`")
        create_tracked_task(delete_later(message, 5))


async def len_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(maxsplit=1)
    target: str | None = (
        parts[1].strip() if len(parts) > 1
        else (message.reply_to_message.text if message.reply_to_message and message.reply_to_message.text else None)
    )
    if not target:
        await message.edit_text("❌ 用法: `.len <文本>` 或回复消息后发 `.len`")
        create_tracked_task(delete_later(message, 5))
        return
    await message.edit_text(
        f"📏 **字数统计**\n\n"
        f"文本: `{target[:30]}{'...' if len(target)>30 else ''}`\n\n"
        f"字符数 (含空格): **{len(target)}**\n"
        f"字符数 (不含空格): **{len(target.replace(' ','').replace(chr(10),''))}**\n"
        f"单词数: **{len(target.split())}**\n"
        f"行数: **{target.count(chr(10))+1}**",
        parse_mode=ParseMode.MARKDOWN,
    )
    create_tracked_task(delete_later(message, 10))


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
        create_tracked_task(delete_later(message))


async def setlang_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(" ", 1)
    if len(parts) > 1:
        save_config("default_lang", parts[1].strip())
        await message.edit_text(f"✅ 默认外语切换为: **{parts[1].strip()}**", parse_mode=ParseMode.MARKDOWN)
        create_tracked_task(delete_later(message))


async def sethome_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(" ", 1)
    if len(parts) > 1:
        save_config("home_lang", parts[1].strip())
        await message.edit_text(
            f"✅ 母语设置为: **{parts[1].strip()}**\nSwap 模式将以此判断翻译方向。",
            parse_mode=ParseMode.MARKDOWN,
        )
        create_tracked_task(delete_later(message))
    else:
        await message.edit_text("❌ 用法: `.sethome zh-CN`")
        create_tracked_task(delete_later(message, 5))


async def addapi_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(maxsplit=4)
    if len(parts) == 5:
        _, name, url, key, model = parts
        config = load_config()
        config["custom_engines"][name.lower()] = {"base_url": url, "api_key": key, "model": model}
        save_config("custom_engines", config["custom_engines"])
        await message.edit_text(f"✅ 添加引擎: `{name}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.edit_text("❌ 用法: `.addapi <名称> <base_url> <api_key> <model>`")
    create_tracked_task(delete_later(message))


async def editapi_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(maxsplit=4)
    if len(parts) == 5:
        _, name, url, key, model = parts
        config = load_config()
        config["custom_engines"][name.lower()] = {"base_url": url, "api_key": key, "model": model}
        save_config("custom_engines", config["custom_engines"])
        await message.edit_text(f"✅ 修改引擎: `{name}`", parse_mode=ParseMode.MARKDOWN)
    create_tracked_task(delete_later(message))


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
    create_tracked_task(delete_later(message))


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
    auto_cmd = config.get("auto_cmd", "")
    if not auto_cmd:
        return
    text = message.text
    parts = auto_cmd.split(" ", 1)
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
