from __future__ import annotations

import re
from functools import lru_cache

from deep_translator import GoogleTranslator

from .config import LESSON_TYPE_MAP

GEORGIAN_RE = re.compile(r"[\u10A0-\u10FF]")

GEORGIAN_TO_LATIN = str.maketrans(
    {
        "ა": "a", "ბ": "b", "გ": "g", "დ": "d", "ე": "e", "ვ": "v", "ზ": "z", "თ": "t",
        "ი": "i", "კ": "k", "ლ": "l", "მ": "m", "ნ": "n", "ო": "o", "პ": "p", "ჟ": "zh",
        "რ": "r", "ს": "s", "ტ": "t", "უ": "u", "ფ": "p", "ქ": "k", "ღ": "gh", "ყ": "q",
        "შ": "sh", "ჩ": "ch", "ც": "ts", "ძ": "dz", "წ": "ts", "ჭ": "ch", "ხ": "kh",
        "ჯ": "j", "ჰ": "h",
    }
)


def has_georgian(text: str) -> bool:
    return bool(GEORGIAN_RE.search(text or ""))


def translate_lesson_type(text: str) -> str:
    for ge, en in LESSON_TYPE_MAP.items():
        if ge in text:
            return en
    return ""


@lru_cache(maxsize=512)
def translate_georgian(text: str) -> str:
    text = (text or "").strip()
    if not text or not has_georgian(text):
        return text
    try:
        return GoogleTranslator(source="ka", target="en").translate(text)
    except Exception:
        return text


def translate_course_line(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return text

    lesson = translate_lesson_type(text)
    translated = translate_georgian(text)

    code_match = re.search(r"\((\d+)\)", text)
    if code_match:
        code = code_match.group(1)
        translated = re.sub(r"\(\d+\)", f"(code {code})", translated)

    if lesson and lesson.lower() not in translated.lower():
        translated = f"{translated} [{lesson}]"

    return translated.strip()


def romanize_georgian(text: str) -> str:
    return text.translate(GEORGIAN_TO_LATIN)


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def name_matches(teacher_name: str, query: str) -> bool:
    query = normalize_name(query)
    if not query:
        return False

    teacher_norm = normalize_name(teacher_name)
    if query in teacher_norm:
        return True

    romanized = normalize_name(romanize_georgian(teacher_name))
    if query in romanized:
        return True

    # Match Latin transliterations embedded in teacher names
    latin_parts = re.findall(r"[A-Za-z]+", teacher_name)
    for part in latin_parts:
        if query in part.lower():
            return True

    return False
