from __future__ import annotations

import io
import re
from typing import Iterable

import pdfplumber

from .html_parser import ScheduleEntry

EXAM_LINE_RE = re.compile(
    r"^(?P<body>.+?)\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+(?P<time>\d{1,2}:\d{2})\s+(?P<room>.+)$"
)
GROUP_PREFIX_RE = re.compile(r"^\d{5}(?:\.\d+)?\s+")
NOISE_LINES = {
    "გამოცდის",
    "დრო",
    "ჯგუფის №",
    "სასწავლო კურსი",
    "პროფესორის გვარი",
    "გამოცდის თარიღი",
    "დაწყების",
    "აუდიტორია",
    "კომპიუტერული ცენტრი",
    "სართული)",
}


def _merge_lines(lines: Iterable[str]) -> list[str]:
    merged: list[str] = []
    buffer = ""

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        if line in NOISE_LINES or line.startswith("შუალედური") or line.endswith("ფაკულტეტი"):
            continue

        candidate = f"{buffer} {line}".strip() if buffer else line
        if EXAM_LINE_RE.match(candidate):
            merged.append(candidate)
            buffer = ""
        elif re.search(r"\d{2}\.\d{2}\.\d{4}", line):
            if buffer:
                merged.append(buffer)
            buffer = line
        else:
            buffer = candidate

    if buffer and EXAM_LINE_RE.match(buffer):
        merged.append(buffer)

    return merged


def _split_teacher(body: str) -> tuple[str, str]:
    body = GROUP_PREFIX_RE.sub("", body).strip()
    words = body.split()
    if len(words) < 3:
        return body, ""

    # Heuristic: last two tokens are surname + first name in Georgian exam PDFs
    teacher = " ".join(words[-2:])
    course = " ".join(words[:-2]).strip()
    return course, teacher


def parse_exam_pdf(pdf_bytes: bytes, faculty: str, source_url: str) -> list[ScheduleEntry]:
    entries: list[ScheduleEntry] = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = text.splitlines()
            for line in _merge_lines(lines):
                match = EXAM_LINE_RE.match(line)
                if not match:
                    continue

                course_raw, teacher = _split_teacher(match.group("body"))
                if not teacher:
                    continue

                entries.append(
                    ScheduleEntry(
                        teacher=teacher,
                        teacher_original=teacher,
                        course=course_raw,
                        course_original=course_raw,
                        day="",
                        time=match.group("time"),
                        room=match.group("room").strip(),
                        group="",
                        source=source_url,
                        schedule_type="exam",
                        faculty=faculty,
                        date=match.group("date"),
                    )
                )

    return entries
