from __future__ import annotations

import re

from .translator import has_georgian

# Values that appear in the professor column but are not people
NOT_A_PERSON = {
    "ტესტირების ცენტრი",
    "კომპიუტერული ცენტრი",
    "კომპ. ცენტრი",
    "კომპიუტერული ცენტრი1",
    "კომპიუტერული ცენტრi",
}

COURSE_HINTS = (
    "საფუძვლ",
    "ისტორი",
    "მათემატიკ",
    "ფიზიკ",
    "ქიმი",
    "გეოდეზ",
    "შესავალი",
    "პრაქტიკ",
    "ლაბორატ",
    "ტექნოლო",
    "ინჟინ",
    "ენა",
    "კურს",
    "ცენტრ",
    "ტესტირ",
    "გრაფიკ",
    "არქიტექტ",
    "პოლიტიკ",
    "ფილოსოფ",
    "სოციოლ",
    "ბიოლოგ",
    "გეოლოგ",
    "მექანიკ",
    "ელექტრ",
    "მარკეტ",
    "ლოგისტ",
    "საბუღალტ",
)


def normalize_person_name(name: str) -> str:
    name = re.sub(r"\s+", " ", (name or "").strip())
    name = name.replace(";", ",")
    # Take first professor when several are listed
    if "," in name:
        name = name.split(",")[0].strip()
    return name


def looks_like_course_title(text: str) -> bool:
    text = (text or "").strip()
    if not text or len(text) < 4:
        return False
    lower = text.lower()
    if any(h in lower for h in COURSE_HINTS):
        return True
    # Long phrases with no person-like structure
    if len(text.split()) >= 5 and not re.search(r"^[ა-ჰ]\.\s*[ა-ჰ]", text):
        return True
    return False


def is_likely_person_name(name: str) -> bool:
    name = normalize_person_name(name)
    if not name or name in NOT_A_PERSON:
        return False
    if looks_like_course_title(name):
        return False
    if name.startswith("(") or name.startswith("["):
        return False
    if len(name) < 3:
        return False
    # Initials like თ. or კ. or ნ.ნიკვაშვილი
    if re.search(r"[ა-ჰ]\.[ა-ჰ]", name):
        return True
    tokens = name.split()
    if len(tokens) >= 2:
        return True
    # Single token only if short (surname-only edge cases)
    return len(tokens) == 1 and len(name) <= 20 and has_georgian(name)
