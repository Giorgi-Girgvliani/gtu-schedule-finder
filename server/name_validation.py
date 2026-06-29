from __future__ import annotations

import re

# Unicode letter ranges for the scripts GTU timetables use.
_GE = r"\u10A0-\u10FF"          # Georgian
_LA = r"A-Za-z\u00C0-\u024F"    # Latin (+ accented)
_CY = r"\u0400-\u04FF"          # Cyrillic
_LETTER = _GE + _LA + _CY

_DIGIT_RE = re.compile(r"\d")
# Structural punctuation that never appears inside a real person name
_STRUCT_RE = re.compile(r"[()\[\]{}/\\+*=:;№#%@!?\"~|<>]")
_LETTER_RUN_RE = re.compile(rf"[{_LETTER}]{{2,}}")
_TOKEN_OK_RE = re.compile(rf"^[{_LETTER}.\-\u2019']+$")
_INITIAL_INLINE_RE = re.compile(rf"[{_LETTER}]\.[{_LETTER}]")

# Exact strings that show up in a "professor" column but are not people.
NOT_A_PERSON = {
    "ტესტირების ცენტრი",
    "კომპიუტერული ცენტრი",
    "კომპ. ცენტრი",
    "კომპიუტერული ცენტრი1",
    "კომპიუტერული ცენტრი",
    "exam center",
    "testing center",
    "computer center",
}

# Substrings that mark a course / subject title (multi-language).
COURSE_HINTS = (
    # Georgian
    "საფუძვლ", "ისტორი", "მათემატიკ", "ანალიზ", "ფიზიკ", "ქიმი", "გეოდეზ",
    "შესავალ", "პრაქტიკ", "ლაბორატ", "ტექნოლო", "ინჟინ", "ენა", "კურს",
    "ცენტრ", "ტესტირ", "გრაფიკ", "არქიტექტ", "პოლიტიკ", "ფილოსოფ", "სოციოლ",
    "ბიოლოგ", "გეოლოგ", "მექანიკ", "ელექტრ", "მარკეტ", "ლოგისტ", "საბუღალტ",
    "დაპროგრამ", "დაპროექტ", "განტოლებ", "ეკონომ", "მართვ", "სისტემ", "დიზაინ",
    "ბიზნეს", "სამართ", "კულტურ", "ფსიქოლ", "ალგორითმ", "მონაცემ", "ქსელ",
    # Russian
    "математик", "физик", "хими", "истори", "культурол", "экономик", "инженер",
    "основы", "технологи", "программир", "анализ", "язык", "ресурс", "сетей",
    "интеракци", "навыки", "бизнес",
    # English
    "mathematic", "physics", "chemistry", "history", "engineering", "drawing",
    "introduction", "fundamentals", "technolog", "programming", "analysis",
    "design", "economic", "management", "advanced", "freehand", "culturolog",
)

# Substrings that mark a room / place rather than a person.
PLACE_HINTS = (
    "auditorium", "building", "корпус", "этаж", "аудитор",
    "აუდიტ", "კორპუს", "სართულ", "ცენტრ",
)


def normalize_person_name(name: str) -> str:
    """Collapse whitespace and keep only the first listed professor."""
    name = re.sub(r"\s+", " ", (name or "").strip())
    name = name.replace(";", ",")
    if "," in name:
        name = name.split(",")[0].strip()
    return name


def _lower(text: str) -> str:
    return (text or "").strip().lower()


def looks_like_place(text: str) -> bool:
    low = _lower(text)
    return any(h in low for h in PLACE_HINTS)


def looks_like_course_title(text: str) -> bool:
    text = (text or "").strip()
    if not text or len(text) < 4:
        return False
    low = text.lower()
    if any(h in low for h in COURSE_HINTS):
        return True
    # A long phrase that is not a "I.Surname" initial form is almost certainly
    # a course title rather than a name.
    if len(text.split()) >= 5 and not _INITIAL_INLINE_RE.search(text):
        return True
    return False


def is_likely_person_name(name: str) -> bool:
    """Strict, language-agnostic check for an actual human name.

    Real GTU lecturer names are short alphabetic strings such as
    "გვარი სახელი", "თ.აბუაშვილი", "Giorgi Mamatelashvili" or bilingual
    duplicates like "დიასამიძე ნუგზარ Диасамидзе Нугзар". They never
    contain digits, parentheses, or course/room keywords.
    """
    name = normalize_person_name(name)
    if not name or name.lower() in NOT_A_PERSON or name in NOT_A_PERSON:
        return False
    # Names never contain digits or structural punctuation.
    if _DIGIT_RE.search(name) or _STRUCT_RE.search(name):
        return False
    if looks_like_course_title(name) or looks_like_place(name):
        return False

    tokens = [t for t in name.split(" ") if t]
    if not tokens:
        return False
    # Every token must be letters (optionally with dots/hyphens for initials).
    if not all(_TOKEN_OK_RE.match(t) for t in tokens):
        return False

    has_initial = bool(_INITIAL_INLINE_RE.search(name)) or any(
        re.fullmatch(rf"[{_LETTER}]\.", t) for t in tokens
    )
    substantial = [t for t in tokens if _LETTER_RUN_RE.search(t)]

    # "I.Surname" or "I. Surname" → initial + at least one real word.
    if has_initial and len(substantial) >= 1:
        return True
    # Otherwise require at least two real words (firstname + surname),
    # which also rejects single-word course names like "Физика".
    return len(substantial) >= 2
