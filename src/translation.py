import asyncio
import logging
import os
import re
from typing import Any

from deep_translator import GoogleTranslator

from .clients import get_gemini_client, get_openai_client, get_custom_client, get_http_client
from .config import load_config

logger = logging.getLogger("translate_bot")

TRANSIENT_ERRORS = (
    UnicodeDecodeError,
    asyncio.TimeoutError,
    ConnectionError,
    OSError,
)


async def _translate_with_retry(
    text: str, target_lang: str, engine: str, config: dict[str, Any], retries: int = 2
) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            return await _translate_with_engine(text, target_lang, engine, config)
        except TRANSIENT_ERRORS as e:
            last_error = e
            if attempt < retries - 1:
                logger.warning("Retry engine=%s attempt=%d error=%s", engine, attempt + 1, e)
                await asyncio.sleep(0.5 * (attempt + 1))
    raise last_error if last_error else Exception("Unknown error")


# ---------------------------------------------------------------------------
# Content protection: extract URLs & emojis before translation, restore after
# ---------------------------------------------------------------------------

_URL_PATTERN = re.compile(
    r'https?://[^\s<>\"\'\)]+|www\.[^\s<>\"\'\)]+'
)

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols extended-A
    "\U00002702-\U000027B0"  # dingbats
    "\U00002600-\U000026FF"  # misc symbols (sun, cloud, etc)
    "\U00002300-\U000023FF"  # misc technical
    "\U0000FE0F"             # variation selector
    "\U0000200D"             # zero width joiner
    "\U00002B50"             # star
    "\U00002B05-\U00002B07"  # arrows
    "\U00002934-\U00002935"  # arrows
    "\U00003030"             # wavy dash
    "\U0000303D"             # part alternation mark
    "\U00003297"             # circled ideograph congratulation
    "\U00003299"             # circled ideograph secret
    "]+",
    re.UNICODE,
)


def _protect_content(text: str) -> tuple[str, dict[str, str]]:
    """Extract URLs and emojis, replace with placeholders to protect from translation."""
    placeholders: dict[str, str] = {}
    counter = 0

    def _replace_url(match: re.Match) -> str:
        nonlocal counter
        key = f"__URL{counter}__"
        placeholders[key] = match.group(0)
        counter += 1
        return key

    def _replace_emoji(match: re.Match) -> str:
        nonlocal counter
        key = f"__EMJ{counter}__"
        placeholders[key] = match.group(0)
        counter += 1
        return key

    protected = _URL_PATTERN.sub(_replace_url, text)
    protected = EMOJI_PATTERN.sub(_replace_emoji, protected)
    return protected, placeholders


def _restore_content(text: str, placeholders: dict[str, str]) -> str:
    """Restore protected URLs and emojis from placeholders."""
    for key, value in placeholders.items():
        text = text.replace(key, value)
    return text


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATE = (
    "你是一个精通多国网络文化的翻译官。\n"
    "【要求】：1. 口吻随性、接地气。 {ja_rule} 3. 俚语替换。"
    " 4. 严禁扭曲原意，必须准确传达语气。 5. 只输出纯翻译结果，无解释。"
    " 6. 严禁添加任何原文中没有的emoji表情符号。"
    " 7. 绝对不要翻译数字/日期/时间，保留原样。"
    " 8. 所有 __URL 和 __EMJ 开头的占位符必须原样保留，不要翻译或修改。\n"
    "【任务】：将以下文本翻译为 [{target_lang_upper}]\n{text}"
)

_JA_RULE = "2. 绝对禁止使用敬体（です/ます）！必须使用常体（だ/である/タ形）。"


def _build_prompt(text: str, target_lang: str) -> str:
    ja_rule = _JA_RULE if target_lang.lower() in ("ja", "jp", "japanese") else ""
    return _PROMPT_TEMPLATE.format(
        ja_rule=ja_rule,
        target_lang_upper=target_lang.upper(),
        target_lang=target_lang,
        text=text,
    )


# ---------------------------------------------------------------------------
# Engine dispatch
# ---------------------------------------------------------------------------

_DEFAULT_TEMPERATURE = 0.8


async def _translate_with_engine(
    text: str, target_lang: str, engine: str, config: dict[str, Any],
) -> str:
    ai_prompt = _build_prompt(text, target_lang)
    logger.info("Translating  engine=%s  target=%s", engine, target_lang)

    if os.getenv("DEBUG"):
        logger.info("PROMPT: %s", ai_prompt)

    if engine == "openai":
        res = await get_openai_client(config).chat.completions.create(
            model=config["models"].get("openai", "gpt-4o-mini"),
            messages=[{"role": "user", "content": ai_prompt}],
            temperature=_DEFAULT_TEMPERATURE,
        )
        return res.choices[0].message.content.strip()

    if engine == "gemini":
        res = await get_gemini_client(config).aio.models.generate_content(
            model=config["models"].get("gemini", "gemini-1.5-flash"),
            contents=ai_prompt,
        )
        return res.text.strip()

    if engine == "google":
        return await asyncio.to_thread(
            lambda: GoogleTranslator(source="auto", target=target_lang).translate(text)
        )

    if engine in config.get("custom_engines", {}):
        cfg = config["custom_engines"][engine]
        client = get_custom_client(cfg)
        res = await client.chat.completions.create(
            model=cfg["model"],
            messages=[{"role": "user", "content": ai_prompt}],
            temperature=_DEFAULT_TEMPERATURE,
        )
        return res.choices[0].message.content.strip()

    raise ValueError(f"Unknown engine: {engine!r}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def translate_text_with_fallback(
    text: str, target_lang: str, preferred_engine: str,
) -> str:
    protected_text, placeholders = _protect_content(text)
    config = load_config()
    seen: set[str] = set()
    engines_to_try: list[str] = []
    for e in [preferred_engine, *config.get("custom_engines", {}).keys(), "gemini", "openai", "google"]:
        if e not in seen:
            seen.add(e)
            engines_to_try.append(e)
    errors: list[str] = []
    for engine in engines_to_try:
        try:
            result = await _translate_with_retry(protected_text, target_lang, engine, config)
            return _restore_content(result, placeholders)
        except Exception as ex:
            logger.warning("Engine %s failed: %s", engine, ex)
            errors.append(f"{engine}({str(ex)[:30]})")
    return f"ERROR: 全部节点崩溃 ({' | '.join(errors[:2])}...)"
