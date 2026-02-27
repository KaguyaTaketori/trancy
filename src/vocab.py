import json
import os
import time
import random
from typing import Any

VOCAB_FILE = "vocab.json"

DEFAULT_VOCAB: dict[str, Any] = {
    "words": [],
    "stats": {
        "total_words": 0,
        "words_learned": 0,
        "quiz_correct": 0,
        "quiz_total": 0,
        "streak_days": 0,
        "last_study_date": "",
        "total_reviews": 0,
    },
}

_vocab_cache: dict[str, Any] | None = None


def load_vocab() -> dict[str, Any]:
    global _vocab_cache
    if _vocab_cache is not None:
        return _vocab_cache
    vocab = {k: v for k, v in DEFAULT_VOCAB.items()}
    if os.path.exists(VOCAB_FILE):
        try:
            with open(VOCAB_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            vocab.update(saved)
        except (json.JSONDecodeError, OSError):
            pass
    _vocab_cache = vocab
    return vocab


def save_vocab() -> None:
    global _vocab_cache
    if _vocab_cache is None:
        return
    try:
        with open(VOCAB_FILE, "w", encoding="utf-8") as f:
            json.dump(_vocab_cache, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _update_streak() -> None:
    vocab = load_vocab()
    stats = vocab.get("stats", {})
    today = time.strftime("%Y-%m-%d")
    last_date = stats.get("last_study_date", "")
    
    if last_date == today:
        return
    
    import datetime
    try:
        last_dt = datetime.datetime.strptime(last_date, "%Y-%m-%d") if last_date else None
        today_dt = datetime.datetime.strptime(today, "%Y-%m-%d")
        
        if last_dt and (today_dt - last_dt).days == 1:
            stats["streak_days"] = stats.get("streak_days", 0) + 1
        elif not last_dt or (today_dt - last_dt).days > 1:
            stats["streak_days"] = 1
    except ValueError:
        stats["streak_days"] = 1
    
    stats["last_study_date"] = today
    vocab["stats"] = stats
    save_vocab()


def add_word(word: str, translation: str, example: str = "", lang: str = "auto") -> dict[str, Any]:
    vocab = load_vocab()
    _update_streak()
    
    word_id = int(time.time() * 1000)
    new_word = {
        "id": word_id,
        "word": word.strip(),
        "translation": translation.strip(),
        "example": example.strip(),
        "lang": lang,
        "created_at": time.time(),
        "next_review": time.time(),
        "interval": 1,
        "ease_factor": 2.5,
        "repetitions": 0,
    }
    
    vocab["words"].insert(0, new_word)
    vocab["stats"]["total_words"] = len(vocab["words"])
    save_vocab()
    return new_word


def delete_word(word_id: int) -> bool:
    vocab = load_vocab()
    original_count = len(vocab["words"])
    vocab["words"] = [w for w in vocab["words"] if w.get("id") != word_id]
    
    if len(vocab["words"]) < original_count:
        vocab["stats"]["total_words"] = len(vocab["words"])
        save_vocab()
        return True
    return False


def get_words(limit: int = 50, lang: str = "") -> list[dict[str, Any]]:
    vocab = load_vocab()
    words = vocab.get("words", [])
    
    if lang:
        words = [w for w in words if w.get("lang") == lang]
    
    return words[:limit]


def get_due_words() -> list[dict[str, Any]]:
    vocab = load_vocab()
    now = time.time()
    return [w for w in vocab.get("words", []) if w.get("next_review", 0) <= now]


def review_word(word_id: int, quality: int) -> dict[str, Any]:
    vocab = load_vocab()
    _update_streak()
    
    for word in vocab["words"]:
        if word.get("id") == word_id:
            if quality >= 3:
                if word.get("repetitions", 0) == 0:
                    word["interval"] = 1
                elif word.get("repetitions", 0) == 1:
                    word["interval"] = 6
                else:
                    word["interval"] = int(word.get("interval", 1) * word.get("ease_factor", 2.5))
                
                word["repetitions"] = word.get("repetitions", 0) + 1
                word["ease_factor"] = max(1.3, word.get("ease_factor", 2.5) + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
            else:
                word["repetitions"] = 0
                word["interval"] = 1
            
            word["next_review"] = time.time() + word["interval"] * 24 * 3600
            vocab["stats"]["total_reviews"] = vocab["stats"].get("total_reviews", 0) + 1
            save_vocab()
            return word
    
    return {}


def get_stats() -> dict[str, Any]:
    vocab = load_vocab()
    stats = vocab.get("stats", {}).copy()
    stats["due_words"] = len(get_due_words())
    stats["total_words"] = len(vocab.get("words", []))
    return stats


def generate_quiz(num_questions: int = 5) -> list[dict[str, Any]]:
    vocab = load_vocab()
    words = [w for w in vocab.get("words", []) if w.get("repetitions", 0) > 0]
    
    if len(words) < 4:
        return []
    
    questions = []
    for _ in range(min(num_questions, len(words) // 3)):
        if not words:
            break
        correct = random.choice(words)
        words.remove(correct)
        
        distractors = random.sample([w for w in vocab["words"] if w["id"] != correct["id"]], min(3, len(vocab["words"]) - 1))
        
        options = [correct] + distractors
        random.shuffle(options)
        
        questions.append({
            "word": correct["word"],
            "correct": correct["translation"],
            "options": [o["translation"] for o in options],
        })
    
    return questions


def record_quiz_result(correct: bool) -> None:
    vocab = load_vocab()
    stats = vocab.get("stats", {})
    
    if correct:
        stats["quiz_correct"] = stats.get("quiz_correct", 0) + 1
    stats["quiz_total"] = stats.get("quiz_total", 0) + 1
    
    vocab["stats"] = stats
    save_vocab()


def check_writing(text: str, target_lang: str) -> dict[str, Any]:
    vocab = load_vocab()
    words = vocab.get("words", [])
    
    results = []
    for word in words:
        if target_lang == word.get("lang", ""):
            if text.lower() == word.get("word", "").lower():
                results.append({
                    "word": word["word"],
                    "translation": word["translation"],
                    "example": word.get("example", ""),
                    "correct": True,
                })
    
    return {
        "checked": text,
        "total_vocab": len(words),
        "target_lang": target_lang,
        "results": results,
    }
