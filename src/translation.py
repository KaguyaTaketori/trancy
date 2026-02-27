import asyncio
import logging
import os
from typing import Any

from deep_translator import GoogleTranslator

from .clients import get_gemini_client, get_openai_client, get_http_client
from src.config import load_config

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


_PROMPT_TEMPLATE = (
    "你是一个精通多国网络文化的翻译官。\n"
    "【要求】：1. 口吻随性、接地气。 {ja_rule} 3. 俚语替换。"
    " 4. 严禁扭曲原意，必须准确传达语气。 5. 只输出纯翻译结果，无解释。"
    " 6. 保留原文的emoji表情符号，不要修改或翻译emoji。"
    " 7. 绝对不要翻译数字/日期/时间，保留原样。\n"
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
            temperature=0.8,
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

    if engine in config["custom_engines"]:
        from openai import AsyncOpenAI
        cfg = config["custom_engines"][engine]
        client = AsyncOpenAI(
            api_key=cfg["api_key"],
            base_url=cfg["base_url"],
            timeout=15.0,
            http_client=get_http_client(),
        )
        res = await client.chat.completions.create(
            model=cfg["model"],
            messages=[{"role": "user", "content": ai_prompt}],
            temperature=0.8,
        )
        return res.choices[0].message.content.strip()

    raise ValueError(f"Unknown engine: {engine!r}")


async def translate_text_with_fallback(
    text: str, target_lang: str, preferred_engine: str,
) -> str:
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
            return await _translate_with_retry(text, target_lang, engine, config)
        except Exception as ex:
            logger.warning("Engine %s failed: %s", engine, ex)
            errors.append(f"{engine}({str(ex)[:30]})")
    return f"ERROR: 全部节点崩溃 ({' | '.join(errors[:2])}...)"
