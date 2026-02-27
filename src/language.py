import re
from functools import lru_cache
from typing import Any

from langdetect import detect as langdetect_detect, LangDetectException

_LANG_ALIASES: dict[str, str] = {
    "zh-cn": "zh-CN", "zh-tw": "zh-TW", "zh": "zh-CN", "jp": "ja",
}

_KO_RE = re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]")
_JA_RE = re.compile(r"[\u3040-\u30FF]")
_AR_RE = re.compile(r"[\u0600-\u06FF]")
_RU_RE = re.compile(r"[\u0400-\u04FF]")
_TH_RE = re.compile(r"[\u0E00-\u0E7F]")
_HE_RE = re.compile(r"[\u0590-\u05FF]")
_CJK_RE = re.compile(r"[\u4E00-\u9FFF]")


def _normalise(lang: str) -> str:
    return _LANG_ALIASES.get(lang.lower(), lang.lower())


@lru_cache(maxsize=512)
def detect_language(text: str) -> str:
    if _KO_RE.search(text):
        return "ko"
    if _JA_RE.search(text):
        return "ja"
    if _AR_RE.search(text):
        return "ar"
    if _RU_RE.search(text):
        return "ru"
    if _TH_RE.search(text):
        return "th"
    if _HE_RE.search(text):
        return "he"
    try:
        return _normalise(langdetect_detect(text))
    except LangDetectException:
        pass
    cjk = len(_CJK_RE.findall(text))
    if cjk / max(len(text.replace(" ", "")), 1) > 0.3:
        return "zh-CN"
    return "unknown"


def is_same_language(text: str, target_lang: str) -> bool:
    detected = detect_language(text)
    norm = _normalise(target_lang)
    if detected.startswith("zh") and norm.startswith("zh"):
        return True
    return detected == norm


def detect_swap_target(text: str, home_lang: str, foreign_lang: str) -> str:
    detected = detect_language(text)
    norm_home = _normalise(home_lang)
    if detected == norm_home or (detected.startswith("zh") and norm_home.startswith("zh")):
        return foreign_lang
    return home_lang
