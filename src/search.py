import asyncio
import logging
import os
import time
from typing import Any

from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException, RatelimitException
from tavily import TavilyClient
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger("translate_bot")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

_search_cache: dict[str, tuple[float, list[dict[str, str]]]] = {}
_CACHE_TTL = 300

_rate_limit_lock = asyncio.Lock()
_last_search_time = 0.0

TRANSIENT_ERRORS = (
    UnicodeDecodeError,
    asyncio.TimeoutError,
    ConnectionError,
)
_min_search_interval = 3.0
_max_retries = 5
_initial_retry_delay = 10.0
_rate_limit_cooldown = 0.0


async def search_web(query: str, max_results: int = 5, page: int = 1) -> list[dict[str, str]]:
    global _last_search_time, _rate_limit_cooldown
    
    cache_key = query.lower().strip()
    
    if cache_key in _search_cache:
        timestamp, cached_results = _search_cache[cache_key]
        if time.monotonic() - timestamp < _CACHE_TTL:
            start = (page - 1) * max_results
            end = start + max_results
            return cached_results[start:end]
    
    if time.monotonic() < _rate_limit_cooldown:
        remaining = int(_rate_limit_cooldown - time.monotonic())
        logger.warning(f"Rate limit cooldown active, {remaining}s remaining")
        return []
    
    async with _rate_limit_lock:
        now = time.monotonic()
        time_since_last = now - _last_search_time
        if time_since_last < _min_search_interval:
            wait_time = _min_search_interval - time_since_last
            logger.info(f"Rate limiting: waiting {wait_time:.2f}s before search")
            await asyncio.sleep(wait_time)
        _last_search_time = time.monotonic()
    
    def _search_ddg() -> list[dict[str, str]]:
        for attempt in range(_max_retries):
            try:
                results = []
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=30, backend="html"):
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "snippet": r.get("body", ""),
                        })
                return results
            except (RatelimitException, DuckDuckGoSearchException):
                if attempt < _max_retries - 1:
                    delay = _initial_retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited by DuckDuckGo, waiting {delay}s before retry (attempt {attempt + 1}/{_max_retries})")
                    time.sleep(delay)
                else:
                    logger.error(f"Rate limit exceeded after {_max_retries} attempts")
                    raise
        return []

    def _search_tavily() -> list[dict[str, str]]:
        if not TAVILY_API_KEY:
            logger.warning("Tavily API key not set")
            return []
        try:
            logger.info(f"Calling Tavily API with key: {TAVILY_API_KEY[:15]}...")
            client = TavilyClient(api_key=TAVILY_API_KEY)
            response = client.search(query=query, max_results=30)
            logger.info(f"Tavily response: {response}")
            results = []
            for r in response.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", ""),
                })
            return results
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
            return []

    try:
        results = await asyncio.to_thread(_search_ddg)
    except (RatelimitException, DuckDuckGoSearchException) as e:
        logger.warning(f"DDG rate limit caught in outer exception: {e}, trying Tavily...")
        results = []
    
    if not results and TAVILY_API_KEY:
        logger.info("DDG returned empty results, trying Tavily fallback...")
        try:
            results = await asyncio.wait_for(asyncio.to_thread(_search_tavily), timeout=30.0)
        except asyncio.TimeoutError:
            logger.warning("Tavily search timed out after 30s")
            results = []
    
    _search_cache[cache_key] = (time.monotonic(), results)
    start = (page - 1) * max_results
    end = start + max_results
    return results[start:end]


def get_all_cached_results(query: str) -> list[dict[str, str]] | None:
    cache_key = query.lower().strip()
    if cache_key in _search_cache:
        timestamp, cached_results = _search_cache[cache_key]
        if time.monotonic() - timestamp < _CACHE_TTL:
            return cached_results
    return None


def get_total_results(query: str) -> int:
    results = get_all_cached_results(query)
    return len(results) if results else 0


async def _summarize_with_engine(query: str, results: list[dict[str, str]], engine: str, config: dict[str, Any]) -> str:
    content_parts = [f"查询: {query}\n\n搜索结果:\n"]
    for i, r in enumerate(results, 1):
        content_parts.append(f"{i}. {r.get('title', '无标题')}")
        content_parts.append(f"   {r.get('snippet', '')[:200]}")
        content_parts.append(f"   来源: {r.get('url', '')}\n")
    
    prompt = f"""请根据以下搜索结果，为用户提供一个简洁的中文总结，包括:
1. 查询的主要答案
2. 关键信息的简要概述

{chr(10).join(content_parts)}

请用简洁的中文总结以上搜索结果（100字以内）:"""

    if engine == "openai":
        from openai import AsyncOpenAI
        from .clients import get_http_client
        client = AsyncOpenAI(
            api_key=config.get("api_keys", {}).get("openai", ""),
            http_client=get_http_client(),
        )
        res = await client.chat.completions.create(
            model=config.get("models", {}).get("openai", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return res.choices[0].message.content.strip()

    if engine == "gemini":
        from .clients import get_gemini_client
        res = await get_gemini_client(config).aio.models.generate_content(
            model=config.get("models", {}).get("gemini", "gemini-1.5-flash"),
            contents=prompt,
        )
        return res.text.strip()

    if engine in config.get("custom_engines", {}):
        from openai import AsyncOpenAI
        from .clients import get_http_client
        cfg = config["custom_engines"][engine]
        client = AsyncOpenAI(
            api_key=cfg["api_key"],
            base_url=cfg["base_url"],
            timeout=30.0,
            http_client=get_http_client(),
        )
        res = await client.chat.completions.create(
            model=cfg["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return res.choices[0].message.content.strip()
    
    raise ValueError(f"Unknown engine: {engine!r}")


async def summarize_results(query: str, results: list[dict[str, str]], engine: str, config: dict[str, Any]) -> str:
    if not results:
        return "❌ 没有搜索结果可供总结"
    
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            return await _summarize_with_engine(query, results, engine, config)
        except TRANSIENT_ERRORS as e:
            last_error = e
            if attempt < 1:
                logger.warning("Retry summarize engine=%s attempt=%d error=%s", engine, attempt + 1, e)
                await asyncio.sleep(0.5)
    
    logger.warning("Summarize failed: %s", last_error)
    return f"❌ 总结失败: {str(last_error)[:50]}" if last_error else "❌ 总结失败"


def format_search_results(results: list[dict[str, str]], query: str, page: int = 1, max_results: int = 5, total: int = 0) -> tuple[str, InlineKeyboardMarkup | None]:
    if not results:
        return "❌ 未找到相关结果", None
    
    start = (page - 1) * max_results + 1
    end = start + len(results) - 1
    page_info = f"📄 第 {page} 页 ({start}-{end})" if total > max_results else ""
    
    lines = [f"🔍 **搜索结果** {page_info}\n"]
    for i, r in enumerate(results, start):
        title = r.get("title", "无标题")[:60]
        url = r.get("url", "")
        snippet = r.get("snippet", "")[:120]
        lines.append(f"**{i}. {title}**")
        lines.append(f"   {snippet}")
        lines.append(f"   🔗 {url}\n")
    
    keyboard = None
    if total > max_results:
        total_pages = (total + max_results - 1) // max_results
        buttons = []
        if page > 1:
            buttons.append(InlineKeyboardButton("◀️ 上一页", callback_data=f"search_{query}_{page - 1}"))
        buttons.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            buttons.append(InlineKeyboardButton("下一页 ▶️", callback_data=f"search_{query}_{page + 1}"))
        keyboard = InlineKeyboardMarkup([buttons])
    
    return "\n".join(lines), keyboard
