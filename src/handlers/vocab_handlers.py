"""Vocabulary, quiz, and writing practice command handlers."""

import datetime
import re
from typing import Any

from pyrogram import Client
from pyrogram.enums import ParseMode

from ..config import load_config
from ..utils import create_tracked_task, delete_later
from ..vocab import (
    add_word,
    check_writing,
    delete_word,
    generate_quiz,
    get_due_words,
    get_stats,
    get_words,
    load_vocab,
    record_quiz_result,
    review_word,
)


def _format_review_card(word: dict[str, Any]) -> str:
    """Build the review card text (shared between vocab review and review response)."""
    next_review = datetime.datetime.fromtimestamp(word.get("next_review", 0))
    next_str = next_review.strftime("%m-%d %H:%M")
    example_text = f"例句: {word['example']}" if word.get("example") else ""
    return (
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
        "5️⃣ 完美记住"
    )


# ---------------------------------------------------------------------------
# Sub-command handlers for .vocab
# ---------------------------------------------------------------------------

async def _vocab_help(message: Any) -> None:
    await message.edit_text(
        "📚 **词汇管理**\n\n"
        "`.vocab add <单词> <翻译> [例句]` — 添加单词\n"
        "`.vocab list [数量]` — 查看词汇表\n"
        "`.vocab del <ID>` — 删除单词\n"
        "`.vocab stats` — 学习统计\n"
        "`.vocab review` — 复习今日单词\n\n"
        "`.quiz` — 开始测验\n"
        "`.write <语言> <文本>` — 写作检查",
        parse_mode=ParseMode.MARKDOWN,
    )
    create_tracked_task(delete_later(message, 20))


async def _vocab_add(message: Any, parts: list[str]) -> None:
    if len(parts) < 4:
        await message.edit_text("❌ 用法: `.vocab add <单词> <翻译> [例句]`")
        create_tracked_task(delete_later(message, 5))
        return

    word = parts[2].strip()
    translation = parts[3].strip()
    example = parts[4].strip() if len(parts) > 4 else ""

    new_word = add_word(word, translation, example)

    example_text = f"例句: {new_word['example']}" if new_word["example"] else ""
    await message.edit_text(
        f"✅ 单词已添加!\n\n"
        f"**{new_word['word']}** — {new_word['translation']}\n"
        f"{example_text}",
        parse_mode=ParseMode.MARKDOWN,
    )
    create_tracked_task(delete_later(message, 15))


async def _vocab_list(message: Any, parts: list[str]) -> None:
    limit = int(parts[2].strip()) if len(parts) > 2 else 20
    words = get_words(limit=limit)

    if not words:
        await message.edit_text("📭 词汇表为空，请先添加单词!")
        create_tracked_task(delete_later(message, 5))
        return

    lines = ["📚 **词汇表**\n"]
    for w in words:
        line = f"`{w['id']}` **{w['word']}** — {w['translation']}"
        if w.get("example"):
            line += f"\n   例: {w['example'][:50]}"
        lines.append(line + "\n")

    await message.edit_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
    create_tracked_task(delete_later(message, 30))


async def _vocab_del(message: Any, parts: list[str]) -> None:
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

    if delete_word(word_id):
        await message.edit_text("✅ 单词已删除")
    else:
        await message.edit_text("❌ 未找到该单词")
    create_tracked_task(delete_later(message, 5))


async def _vocab_stats(message: Any) -> None:
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
        parse_mode=ParseMode.MARKDOWN,
    )
    create_tracked_task(delete_later(message, 20))


async def _vocab_review(message: Any) -> None:
    due = get_due_words()

    if not due:
        await message.edit_text("✅ 暂无待复习单词!")
        create_tracked_task(delete_later(message, 5))
        return

    await message.edit_text(_format_review_card(due[0]), parse_mode=ParseMode.MARKDOWN)


_VOCAB_ACTIONS = {
    "add": lambda msg, parts: _vocab_add(msg, parts),
    "list": lambda msg, parts: _vocab_list(msg, parts),
    "del": lambda msg, parts: _vocab_del(msg, parts),
    "stats": lambda msg, _: _vocab_stats(msg),
    "review": lambda msg, _: _vocab_review(msg),
}


# ---------------------------------------------------------------------------
# Public command handlers
# ---------------------------------------------------------------------------

async def vocab_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(maxsplit=3)

    if len(parts) == 1:
        await _vocab_help(message)
        return

    action = parts[1].strip().lower()
    handler = _VOCAB_ACTIONS.get(action)
    if handler:
        await handler(message, parts)
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

    match = re.search(r'\n\n\*\*([^*]+)\*\*\n', reply_text)
    if not match:
        return

    word_text = match.group(1)

    words = get_words(limit=100)
    for w in words:
        if w.get("word") == word_text:
            review_word(w["id"], quality)
            break

    due = get_due_words()
    if due:
        await message.edit_text(_format_review_card(due[0]), parse_mode=ParseMode.MARKDOWN)
    else:
        await message.edit_text("✅ 恭喜! 所有单词都已复习完毕!")
        create_tracked_task(delete_later(message, 5))


async def quiz_cmd(client: Client, message: Any) -> None:
    vocab = load_vocab()
    words = [w for w in vocab.get("words", []) if w.get("repetitions", 0) > 0]

    if len(words) < 4:
        await message.edit_text(
            "❌ 词汇量不足，需要至少 4 个已学习的单词才能开始测验\n"
            "请先使用 `.vocab add` 添加单词，并用 `.vocab review` 复习几次",
            parse_mode=ParseMode.MARKDOWN,
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
        parse_mode=ParseMode.MARKDOWN,
    )


async def write_cmd(client: Client, message: Any) -> None:
    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        await message.edit_text("❌ 用法: `.write <语言> <文本>`\n例: `.write ja こんにちは`")
        create_tracked_task(delete_later(message, 5))
        return

    lang = parts[1].strip().lower()
    text = parts[2].strip()

    result = check_writing(text, lang)

    if result["results"]:
        r = result["results"][0]
        example_text = f"例句: {r['example']}" if r.get("example") else ""
        await message.edit_text(
            f"✅ **写作检查**\n\n"
            f"你写的: **{text}**\n"
            f"翻译: {r['translation']}\n"
            f"{example_text}",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await message.edit_text(
            f"❓ **写作检查**\n\n"
            f"你写的: **{text}**\n\n"
            f"该语言词汇库中没有找到匹配\n"
            f"总词汇量: {result['total_vocab']}",
            parse_mode=ParseMode.MARKDOWN,
        )
    create_tracked_task(delete_later(message, 15))
