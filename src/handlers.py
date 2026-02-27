import asyncio
import time
from typing import Any

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .clients import clear_clients
from src.config import load_config, save_config
from .language import detect_language, detect_swap_target, is_same_language
from .translation import _translate_with_engine, translate_text_with_fallback
from .utils import create_tracked_task, delete_later
from . import vocab


HELP_MAIN = """\
🤖 **高可用多语翻译网关**

⚙️ 引擎: `{engine}` | 🌐 母语: `{home_lang}` | 默认外语: `{default_lang}`
🔄 自动模式: {auto_status}

选择下方按钮查看对应命令"""



async def help_cmd(client: Client, message: Any) -> None:
    config = load_config()
    engine = config.get("engine", "gemini")
    home_lang = config.get("home_lang", "zh-CN")
    default_lang = config.get("default_lang", "ja")
    auto = config.get("auto_cmd", "")
    auto_status = f"✅ `.{auto}`" if auto else "❌ 关闭"

    help_text = HELP_MAIN.format(
        engine=engine,
        home_lang=home_lang,
        default_lang=default_lang,
        auto_status=auto_status,
    )
    
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("📝 翻译", callback_data="help_trans"),
            InlineKeyboardButton("🔄 自动", callback_data="help_auto"),
        ], [
            InlineKeyboardButton("📋 工具", callback_data="help_tool"),
            InlineKeyboardButton("⚙️ 设置", callback_data="help_set"),
        ], [
            InlineKeyboardButton("📚 词汇", callback_data="help_vocab"),
            InlineKeyboardButton("🎯 测验", callback_data="help_quiz"),
        ]]
    )
    await message.edit_text(help_text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


HELP_TRANS = """\
📝 **翻译命令**

`.tr <文本>` — 翻译为默认外语
  例: `.tr 今天天气真好`

`.t <语言> <文本>` — 翻译为指定语言
  例: `.t en 你好世界`
  例: `.t ja,ko,en 你好`

`.rr <文本>` — 替换为默认外语

`.r <语言> <文本>` — 替换为指定语言

`.tl` — 翻译回复的消息（译为母语）"""

HELP_AUTO = """\
🔄 **自动模式**

`.auto swap` — 🌟 智能双向互译
  发中文 → 自动追加外语
  发外语 → 自动追加中文

`.auto tr` — 追加默认外语
`.auto rr` — 替换为默认外语
`.auto t ja` — 追加指定语言
`.auto off` — 关闭"""

HELP_TOOL = """\
📋 **消息工具**

`.detect` — 识别语言
  例: `.detect 你好` → `zh`

`.ping` — 测试引擎延迟

`.copy` — 复制回复的消息

`.len` — 统计字数"""

HELP_SET = """\
⚙️ **系统设置**

`.setlang <代码>` — 默认外语
  例: `.setlang ko`

`.sethome <代码>` — 母语
  例: `.sethome zh-CN`

`.setengine <名称>` — 切换引擎
  可选: gemini / openai / google

`.setmodel <模型>` — 修改模型

`.setkey <引擎> <Key>` — 更新 API Key

`.addapi <名> <URL> <Key> <模型>` — 添加引擎"""

HELP_VOCAB = """\
📚 **词汇学习**

`.vocab add <单词> <翻译> [例句]` — 添加
  例: `.vocab add 猫 cat`

`.vocab list [数量]` — 查看列表

`.vocab del <ID>` — 删除

`.vocab stats` — 学习统计

`.vocab review` — 复习单词"""

HELP_QUIZ = """\
🎯 **测验练习**

`.quiz` — 单词测验
  需要至少 4 个已复习单词

`.write <语言> <文本>` — 写作检查
  例: `.write ja こんにちは`"""


async def help_callback(client: Client, callback_query: Any) -> None:
    data = callback_query.data
    
    if data == "help_trans":
        text = HELP_TRANS
    elif data == "help_auto":
        text = HELP_AUTO
    elif data == "help_tool":
        text = HELP_TOOL
    elif data == "help_set":
        text = HELP_SET
    elif data == "help_vocab":
        text = HELP_VOCAB
    elif data == "help_quiz":
        text = HELP_QUIZ
    else:
        await callback_query.answer()
        return
    
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("📝 翻译", callback_data="help_trans"),
            InlineKeyboardButton("🔄 自动", callback_data="help_auto"),
        ], [
            InlineKeyboardButton("📋 工具", callback_data="help_tool"),
            InlineKeyboardButton("⚙️ 设置", callback_data="help_set"),
        ], [
            InlineKeyboardButton("📚 词汇", callback_data="help_vocab"),
            InlineKeyboardButton("🎯 测验", callback_data="help_quiz"),
        ]]
    )
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    await callback_query.answer()


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


async def vocab_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(maxsplit=3)
    
    if len(parts) == 1:
        await message.edit_text(
            "📚 **词汇管理**\n\n"
            "`.vocab add <单词> <翻译> [例句]` — 添加单词\n"
            "`.vocab list [数量]` — 查看词汇表\n"
            "`.vocab del <ID>` — 删除单词\n"
            "`.vocab stats` — 学习统计\n"
            "`.vocab review` — 复习今日单词\n\n"
            "`.quiz` — 开始测验\n"
            "`.write <语言> <文本>` — 写作检查",
            parse_mode=ParseMode.MARKDOWN
        )
        create_tracked_task(delete_later(message, 20))
        return
    
    action = parts[1].strip().lower()
    
    if action == "add":
        if len(parts) < 4:
            await message.edit_text("❌ 用法: `.vocab add <单词> <翻译> [例句]`")
            create_tracked_task(delete_later(message, 5))
            return
        
        word = parts[2].strip()
        translation = parts[3].strip()
        example = parts[4].strip() if len(parts) > 4 else ""
        
        from .vocab import add_word
        new_word = add_word(word, translation, example)
        
        example_text = f"例句: {new_word['example']}" if new_word['example'] else ""
        await message.edit_text(
            f"✅ 单词已添加!\n\n"
            f"**{new_word['word']}** — {new_word['translation']}\n"
            f"{example_text}",
            parse_mode=ParseMode.MARKDOWN
        )
        create_tracked_task(delete_later(message, 15))
    
    elif action == "list":
        from .vocab import get_words
        limit = int(parts[2].strip()) if len(parts) > 2 else 20
        words = get_words(limit=limit)
        
        if not words:
            await message.edit_text("📭 词汇表为空，请先添加单词!")
            create_tracked_task(delete_later(message, 5))
            return
        
        lines = ["📚 **词汇表**\n"]
        for w in words:
            lines.append(f"`{w['id']}` **{w['word']}** — {w['translation']}")
            if w.get("example"):
                lines[-1] += f"\n   例: {w['example'][:50]}"
            lines[-1] += "\n"
        
        await message.edit_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
        create_tracked_task(delete_later(message, 30))
    
    elif action == "del":
        if len(parts) < 3:
            await message.edit_text("❌ 用法: `.vocab del <ID>`")
            create_tracked_task(delete_later(message, 5))
            return
        
        try:
            word_id = int(parts[2].strip())
        except ValueError:
            await message.edit_text("❌ ID 必须是数字")
            create_tracked_task(delete_later(message, 5))
            return
        
        from .vocab import delete_word
        if delete_word(word_id):
            await message.edit_text("✅ 单词已删除")
        else:
            await message.edit_text("❌ 未找到该单词")
        create_tracked_task(delete_later(message, 5))
    
    elif action == "stats":
        from .vocab import get_stats
        stats = get_stats()
        
        accuracy = 0
        if stats.get("quiz_total", 0) > 0:
            accuracy = int(stats["quiz_correct"] / stats["quiz_total"] * 100)
        
        await message.edit_text(
            "📊 **学习统计**\n\n"
            f"📚 总单词数: **{stats.get('total_words', 0)}**\n"
            f"📝 待复习: **{stats.get('due_words', 0)}**\n"
            f"🔄 复习次数: **{stats.get('total_reviews', 0)}**\n\n"
            f"✅ 测验正确率: **{accuracy}%** ({stats.get('quiz_correct', 0)}/{stats.get('quiz_total', 0)})\n"
            f"🔥 连续学习: **{stats.get('streak_days', 0)}** 天",
            parse_mode=ParseMode.MARKDOWN
        )
        create_tracked_task(delete_later(message, 20))
    
    elif action == "review":
        from .vocab import get_due_words
        due = get_due_words()
        
        if not due:
            await message.edit_text("✅ 暂无待复习单词!")
            create_tracked_task(delete_later(message, 5))
            return
        
        word = due[0]
        import datetime
        next_review = datetime.datetime.fromtimestamp(word.get("next_review", 0))
        next_str = next_review.strftime("%m-%d %H:%M")
        example_text = f"例句: {word['example']}" if word.get('example') else ""
        
        await message.edit_text(
            f"📖 **复习单词**\n\n"
            f"**{word['word']}**\n\n"
            f"翻译: ||{word['translation']}||\n"
            f"{example_text}\n\n"
            f"⏰ 下次复习: {next_str}\n\n"
            "回复数字评分:\n"
            "1️⃣ 完全忘记\n"
            "2️⃣ 记得但不确定\n"
            "3️⃣ 记得但反应慢\n"
            "4️⃣ 记得很清楚\n"
            "5️⃣ 完美记住",
            parse_mode=ParseMode.MARKDOWN
        )
    
    else:
        await message.edit_text("❌ 未知命令，可用: add, list, del, stats, review")
        create_tracked_task(delete_later(message, 5))


async def vocab_review_response(client: Client, message: Any) -> None:
    if not message.reply_to_message or not message.reply_to_message.text:
        return
    
    reply_text = message.reply_to_message.text
    if "📖 **复习单词**" not in reply_text:
        return
    
    try:
        quality = int(message.text.strip())
        if quality < 1 or quality > 5:
            return
    except ValueError:
        return
    
    import re
    match = re.search(r'\n\n\*\*([^*]+)\*\*\n', reply_text)
    if not match:
        return
    
    word_text = match.group(1)
    
    from .vocab import get_words, review_word, get_due_words
    words = get_words(limit=100)
    for w in words:
        if w.get("word") == word_text:
            review_word(w["id"], quality)
            break
    
    due = get_due_words()
    if due:
        word = due[0]
        import datetime
        next_review = datetime.datetime.fromtimestamp(word.get("next_review", 0))
        next_str = next_review.strftime("%m-%d %H:%M")
        example_text = f"例句: {word['example']}" if word.get('example') else ""
        
        await message.edit_text(
            f"📖 **复习单词**\n\n"
            f"**{word['word']}**\n\n"
            f"翻译: ||{word['translation']}||\n"
            f"{example_text}\n\n"
            f"⏰ 下次复习: {next_str}\n\n"
            "回复数字评分:\n"
            "1️⃣ 完全忘记\n"
            "2️⃣ 记得但不确定\n"
            "3️⃣ 记得但反应慢\n"
            "4️⃣ 记得很清楚\n"
            "5️⃣ 完美记住",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.edit_text("✅ 恭喜! 所有单词都已复习完毕!")
        create_tracked_task(delete_later(message, 5))


async def quiz_cmd(client: Client, message: Any) -> None:
    from .vocab import generate_quiz, record_quiz_result, load_vocab
    
    vocab = load_vocab()
    words = [w for w in vocab.get("words", []) if w.get("repetitions", 0) > 0]
    
    if len(words) < 4:
        await message.edit_text(
            "❌ 词汇量不足，需要至少 4 个已学习的单词才能开始测验\n"
            "请先使用 `.vocab add` 添加单词，并用 `.vocab review` 复习几次",
            parse_mode=ParseMode.MARKDOWN
        )
        create_tracked_task(delete_later(message, 10))
        return
    
    questions = generate_quiz(num_questions=5)
    
    if not questions:
        await message.edit_text("❌ 无法生成测验，请先复习一些单词")
        create_tracked_task(delete_later(message, 5))
        return
    
    q = questions[0]
    options_text = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(q["options"]))
    
    await message.edit_text(
        f"📝 **测验** (1/{len(questions)})\n\n"
        f"**{q['word']}** 的翻译是?\n\n{options_text}\n\n"
        "回复数字选择答案",
        parse_mode=ParseMode.MARKDOWN
    )


async def write_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(maxsplit=2)
    
    if len(parts) < 3:
        await message.edit_text("❌ 用法: `.write <语言> <文本>`\n例: `.write ja こんにちは`")
        create_tracked_task(delete_later(message, 5))
        return
    
    lang = parts[1].strip().lower()
    text = parts[2].strip()
    
    from .vocab import check_writing
    result = check_writing(text, lang)
    
    if result["results"]:
        r = result["results"][0]
        example_text = f"例句: {r['example']}" if r.get('example') else ""
        await message.edit_text(
            f"✅ **写作检查**\n\n"
            f"你写的: **{text}**\n"
            f"翻译: {r['translation']}\n"
            f"{example_text}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.edit_text(
            f"❓ **写作检查**\n\n"
            f"你写的: **{text}**\n\n"
            f"该语言词汇库中没有找到匹配\n"
            f"总词汇量: {result['total_vocab']}",
            parse_mode=ParseMode.MARKDOWN
        )
    create_tracked_task(delete_later(message, 15))
