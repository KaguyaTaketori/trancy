"""Utility command handlers: help, status, ping, detect, copy, len."""

import asyncio
import time
from typing import Any

from pyrogram import Client
from pyrogram.enums import ParseMode

from ..config import load_config
from ..language import detect_language
from ..translation import _translate_with_engine
from ..utils import create_tracked_task, delete_later


HELP_TEXT = """\
🤖 **高可用多语翻译网关 · 完整指令手册**
⚙️ 引擎: `{engine}` · 模型: `{model_display}`
🌐 母语: `{home_lang}` · 默认外语: `{default_lang}`
🔄 自动模式: {auto_status}
🔌 自定义引擎: `{custom_list}`

━━━━━━━━━━━━━━━━━━━━━━
📝 **基础翻译 · 追加模式**
翻译结果追加在原文下方

`.tr <文本>` — 翻译为默认外语
  例: `.tr 今天天气真好`

`.t <语言> <文本>` — 翻译为指定语言
  例: `.t en 你好世界`
  例: `.t ja,ko,en 你好` ← 同时译多语

━━━━━━━━━━━━━━━━━━━━━━
🔄 **基础翻译 · 替换模式**
原文被翻译结果完全替换

`.rr <文本>` — 替换为默认外语
  例: `.rr 今天天气真好`

`.r <语言> <文本>` — 替换为指定语言
  例: `.r ja 我喜欢猫`

━━━━━━━━━━━━━━━━━━━━━━
💬 **翻译他人消息**

`.tl` — 翻译你正在回复的消息（译为母语）
  先回复一条消息，再发 `.tl`

━━━━━━━━━━━━━━━━━━━━━━
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

━━━━━━━━━━━━━━━━━━━━━━
🔍 **检测与诊断**

`.detect` — 准确识别语言
  例: `.detect 多分風` → `ja` ✅
  或: 回复消息后发 `.detect`

`.ping` — 测试所有引擎延迟
`.status` — 查看所有当前配置

━━━━━━━━━━━━━━━━━━━━━━
📋 **消息工具**

`.copy` — 复制回复消息的原文
  先回复一条消息，再发 `.copy`

`.len` — 统计字数/字符数
  例: `.len 你好世界` 或回复后发 `.len`

━━━━━━━━━━━━━━━━━━━━━━
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

━━━━━━━━━━━━━━━━━━━━━━
🔌 **自定义引擎 (兼容 OpenAI API 格式)**

`.addapi <名> <URL> <Key> <模型>` — 添加
  例: `.addapi grok https://api.x.ai/v1 xai-xxx grok-3`

`.editapi <名> <URL> <Key> <模型>` — 修改
`.delapi <名>` — 删除

━━━━━━━━━━━━━━━━━━━━━━
📚 **词汇学习**

`.vocab add <单词> <翻译> [例句]` — 添加单词
  例: `.vocab add 猫 cat`
  例: `.vocab add 食べる たべる 吃饭`

`.vocab list [数量]` — 查看词汇表
  例: `.vocab list 20`

`.vocab del <ID>` — 删除单词
  例: `.vocab del 1234567890`

`.vocab stats` — 学习统计

`.vocab review` — 复习今日单词 (艾宾浩斯遗忘曲线)

━━━━━━━━━━━━━━━━━━━━━━
🎯 **测验与练习**

`.quiz` — 单词测验 (选择题)
  需要至少 4 个已复习过的单词

`.write <语言> <文本>` — 写作检查
  例: `.write ja こんにちは`

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
