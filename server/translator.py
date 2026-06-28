from __future__ import annotations

import re
from functools import lru_cache

from deep_translator import GoogleTranslator

from .config import LESSON_TYPE_MAP

GEORGIAN_RE = re.compile(r"[\u10A0-\u10FF]")

# Canonical one-char-per-letter mapping used for romanization
GEORGIAN_TO_LATIN = str.maketrans(
    {
        "ა": "a", "ბ": "b", "გ": "g", "დ": "d", "ე": "e", "ვ": "v", "ზ": "z", "თ": "t",
        "ი": "i", "კ": "k", "ლ": "l", "მ": "m", "ნ": "n", "ო": "o", "პ": "p", "ჟ": "zh",
        "რ": "r", "ს": "s", "ტ": "t", "უ": "u", "ფ": "p", "ქ": "k", "ღ": "gh", "ყ": "q",
        "შ": "sh", "ჩ": "ch", "ც": "ts", "ძ": "dz", "წ": "ts", "ჭ": "ch", "ხ": "kh",
        "ჯ": "j", "ჰ": "h",
    }
)

# Placeholder chars that won't appear in normal names — used to collapse
# multi-char digraphs before handling single-char variants.
_KH  = "\x10"  # ხ  (kh / x)
_SH  = "\x11"  # შ  (sh)
_CH  = "\x12"  # ჩ/ჭ (ch / tch)
_TS  = "\x13"  # ც/წ (ts / c)
_DZ  = "\x14"  # ძ  (dz)
_ZH  = "\x15"  # ჟ  (zh / j)
_GH  = "\x16"  # ღ  (gh)


def _normalize_translit_variants(text: str) -> str:
    """Collapse common Georgian romanisation variants to unique placeholders.

    Handles both the digraph form (kh, sh, ts …) and the single-letter
    shortcuts that people sometimes use (x for kh, c for ts, etc.).
    The result is only meaningful for comparison, never for display.
    """
    # Multi-char digraphs first (order matters to avoid partial replacement)
    text = text.replace("kh", _KH)
    text = text.replace("sh", _SH)
    text = text.replace("ch", _CH)
    text = text.replace("ts", _TS)
    text = text.replace("dz", _DZ)
    text = text.replace("zh", _ZH)
    text = text.replace("gh", _GH)
    # Single-char shorthand variants
    text = text.replace("c", _TS)   # c as alternative for ც/წ
    text = text.replace("x", _KH)   # x as alternative for ხ
    text = text.replace("w", _TS)   # w sometimes used for წ
    return text


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


def transliteration_key(name: str) -> str:
    """Canonical key for deduplicating names that appear in both Georgian
    script and various Latin transliterations.

    Two names produce the same key when they differ only in:
    - Georgian vs Latin script (romanisation)
    - Word order  (firstname/surname conventions differ between sources)
    - Common transliteration variants: ts/c for ც, kh/x for ხ, etc.
    """
    # Romanise any Georgian characters, then lower-case
    romanized = normalize_name(romanize_georgian(name))
    # Collapse transliteration variants
    normalized = _normalize_translit_variants(romanized)
    # Sort tokens so word-order differences become irrelevant
    tokens = sorted(normalized.split())
    return " ".join(tokens)


def name_matches(teacher_name: str, query: str) -> bool:
    """Return True if *query* plausibly refers to *teacher_name*.

    Handles:
    - Direct substring match (Georgian or Latin)
    - Georgian teacher name searched with Latin transliteration
    - Latin teacher name searched with Georgian script
    - Transliteration variants (ts/c for ც, kh for ხ, etc.)
    - Word-order differences are NOT handled here (search is substring-based)
    """
    query_norm = normalize_name(query)
    if not query_norm:
        return False

    teacher_norm = normalize_name(teacher_name)

    # 1. Direct substring (covers identical-script cases)
    if query_norm in teacher_norm:
        return True

    # 2. Romanise the teacher name, compare against raw query
    #    (Georgian teacher searched with Latin text)
    romanized_teacher = normalize_name(romanize_georgian(teacher_name))
    if query_norm in romanized_teacher:
        return True

    # 3. Romanise the query, compare against teacher name
    #    (Latin teacher name searched with Georgian text)
    romanized_query = normalize_name(romanize_georgian(query))
    if romanized_query != query_norm:
        if romanized_query in teacher_norm:
            return True
        if romanized_query in romanized_teacher:
            return True

    # 4. Normalise transliteration variants for both sides, then compare
    #    (catches ts/c, kh/x, etc.)
    norm_teacher = _normalize_translit_variants(romanized_teacher)
    # Build the normalised query from whichever romanised form is richer
    q_for_norm = romanized_query if romanized_query != query_norm else query_norm
    norm_query = _normalize_translit_variants(q_for_norm)
    if norm_query and norm_query in norm_teacher:
        return True

    # 5. Latin parts embedded in the teacher name (e.g. mixed-script entries)
    latin_parts = re.findall(r"[A-Za-z]+", teacher_name)
    for part in latin_parts:
        if query_norm in part.lower():
            return True

    return False
