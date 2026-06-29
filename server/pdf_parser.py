from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Callable

import pdfplumber

from .html_parser import ScheduleEntry
from .name_validation import is_likely_person_name, looks_like_course_title, normalize_person_name

# --- shared patterns ---

DATE_NUMERIC = re.compile(r"(\d{2}\.\d{2}\.\d{4})")
TIME_RE = re.compile(r"(\d{1,2}:\d{2})")
GROUP_RE = re.compile(r"^\d{4,6}(?:\.\d+)?$")

GEORGIAN_MONTHS = {
    "იანვარი": 1,
    "თებერვალი": 2,
    "მარტი": 3,
    "აპრილი": 4,
    "მაისი": 5,
    "ივნისი": 6,
    "ივლისი": 7,
    "აგვისტო": 8,
    "სექტემბერი": 9,
    "ოქტომბერი": 10,
    "ნოემბერი": 11,
    "დეკემბერი": 12,
}

HEADER_MARKERS = ("კურს", "გვარი", "თარიღ", "აუდიტ")


@dataclass
class ParseResult:
    strategy: str
    entries: list[ScheduleEntry]
    score: float
    stats: dict


def _clean_cell(value) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\n", " ")).strip()


def _parse_georgian_date(text: str) -> str:
    text = text or ""
    m = DATE_NUMERIC.search(text)
    if m:
        return m.group(1)
    # e.g. "სამშაბათი, 30 ივნისი, 2026 წელი" or "04 ივლისი, 2026"
    for month_name, month_num in GEORGIAN_MONTHS.items():
        if month_name in text:
            dm = re.search(rf"(\d{{1,2}})\s*{re.escape(month_name)}", text)
            ym = re.search(r"(20\d{2})", text)
            if dm and ym:
                return f"{int(dm.group(1)):02d}.{month_num:02d}.{ym.group(1)}"
    return ""


def _extract_time(text: str) -> str:
    m = TIME_RE.search(text or "")
    return m.group(1) if m else ""


def _score_entries(entries: list[ScheduleEntry]) -> tuple[float, dict]:
    if not entries:
        return 0.0, {"count": 0}

    with_teacher = sum(1 for e in entries if e.teacher_original)
    valid_teacher = sum(1 for e in entries if e.teacher_original and is_likely_person_name(e.teacher_original))
    with_date = sum(1 for e in entries if e.date)
    with_course = sum(1 for e in entries if e.course_original and not looks_like_course_title(e.teacher_original))
    bad_teacher = sum(
        1 for e in entries
        if e.teacher_original and not is_likely_person_name(e.teacher_original)
    )
    course_as_teacher = sum(
        1 for e in entries
        if e.teacher_original and looks_like_course_title(e.teacher_original)
    )

    n = len(entries)
    stats = {
        "count": n,
        "valid_teacher": valid_teacher,
        "bad_teacher": bad_teacher,
        "course_as_teacher": course_as_teacher,
        "with_date": with_date,
    }

    if n == 0:
        return 0.0, stats

    score = (
        (valid_teacher / n) * 50
        + (with_date / n) * 25
        + (with_course / n) * 15
        + min(n / 20, 1.0) * 10
        - (course_as_teacher / n) * 40
        - (bad_teacher / n) * 20
    )
    return max(score, 0.0), stats


def _row_is_header(cells: list[str]) -> bool:
    joined = " ".join(cells).lower()
    hits = sum(1 for m in HEADER_MARKERS if m in joined)
    return hits >= 2


def _map_columns(header: list[str]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for i, cell in enumerate(header):
        c = cell.lower()
        if "ჯგუფ" in c or c in {"№", "no", "#"}:
            mapping["group"] = i
        elif "კურს" in c:
            mapping["course"] = i
        elif "გვარი" in c or "პროფ" in c:
            mapping["teacher"] = i
        elif "თარიღ" in c:
            mapping["date"] = i
        elif "დრო" in c:
            mapping["time"] = i
        elif "აუდიტ" in c:
            mapping["room"] = i
    # Default GTU layout when headers are messy
    if "course" not in mapping and len(header) >= 6:
        mapping.setdefault("group", 0)
        mapping.setdefault("course", 1)
        mapping.setdefault("teacher", 2)
        mapping.setdefault("date", 3)
        mapping.setdefault("time", 4)
        mapping.setdefault("room", 5)
    return mapping


def _entry_from_row(
    row: list[str],
    cols: dict[str, int],
    *,
    faculty: str,
    source_url: str,
    current_group: str,
) -> tuple[ScheduleEntry | None, str]:
    def cell(key: str) -> str:
        idx = cols.get(key, -1)
        if idx < 0 or idx >= len(row):
            return ""
        return _clean_cell(row[idx])

    group = cell("group") or current_group
    if group and GROUP_RE.match(group):
        current_group = group
    elif not group:
        group = current_group

    course = cell("course")
    teacher_raw = normalize_person_name(cell("teacher"))
    date_raw = cell("date")
    time_raw = cell("time")
    room = cell("room")

    if not course and not teacher_raw:
        return None, current_group

    if not course:
        return None, current_group

    date = _parse_georgian_date(date_raw)
    time = _extract_time(time_raw) or _extract_time(date_raw)

    teacher = teacher_raw if is_likely_person_name(teacher_raw) else ""

    return (
        ScheduleEntry(
            teacher=teacher or "",
            teacher_original=teacher or "",
            course=course,
            course_original=course,
            day="",
            time=time,
            room=room,
            group=group,
            source=source_url,
            schedule_type="exam",
            faculty=faculty,
            date=date,
        ),
        current_group,
    )


def parse_tables(pdf_bytes: bytes, faculty: str, source_url: str) -> list[ScheduleEntry]:
    entries: list[ScheduleEntry] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                if not table or len(table) < 2:
                    continue
                cols: dict[str, int] | None = None
                current_group = ""
                for row in table:
                    cells = [_clean_cell(c) for c in row]
                    if not any(cells):
                        continue
                    if cols is None or _row_is_header(cells):
                        if _row_is_header(cells):
                            cols = _map_columns(cells)
                        continue
                    if cols is None:
                        continue
                    entry, current_group = _entry_from_row(
                        cells, cols, faculty=faculty, source_url=source_url, current_group=current_group
                    )
                    if entry:
                        entries.append(entry)
    return entries


# --- legacy text-line parser (kept as fallback) ---

EXAM_LINE_RE = re.compile(
    r"^(?P<body>.+?)\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+(?P<time>\d{1,2}:\d{2})\s+(?P<room>.+)$"
)
GROUP_PREFIX_RE = re.compile(r"^\d{5}(?:\.\d+)?\s+")
NOISE_LINES = {
    "გამოცდის", "დრო", "ჯგუფის №", "სასწავლო კურსი", "პროფესორის გვარი",
    "გამოცდის თარიღი", "დაწყების", "აუდიტორია", "კომპიუტერული ცენტრი", "სართული)",
}


def _merge_lines(lines) -> list[str]:
    merged, buffer = [], ""
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
    teacher = normalize_person_name(" ".join(words[-2:]))
    course = " ".join(words[:-2]).strip()
    if not is_likely_person_name(teacher):
        return body, ""
    return course, teacher


def parse_text_lines(pdf_bytes: bytes, faculty: str, source_url: str) -> list[ScheduleEntry]:
    entries: list[ScheduleEntry] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in _merge_lines(text.splitlines()):
                match = EXAM_LINE_RE.match(line)
                if not match:
                    continue
                course_raw, teacher = _split_teacher(match.group("body"))
                if not course_raw:
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


STRATEGIES: list[tuple[str, Callable[..., list[ScheduleEntry]]]] = [
    ("tables", parse_tables),
    ("text_lines", parse_text_lines),
]


def parse_exam_pdf(pdf_bytes: bytes, faculty: str, source_url: str) -> list[ScheduleEntry]:
    """Try each parsing strategy and return results from the best-scoring one."""
    return parse_exam_pdf_with_meta(pdf_bytes, faculty, source_url).entries


def parse_exam_pdf_with_meta(pdf_bytes: bytes, faculty: str, source_url: str) -> ParseResult:
    """Try each parsing strategy; return entries plus chosen strategy and score."""
    best: ParseResult | None = None

    for name, fn in STRATEGIES:
        try:
            entries = fn(pdf_bytes, faculty, source_url)
            score, stats = _score_entries(entries)
            result = ParseResult(strategy=name, entries=entries, score=score, stats=stats)
            if best is None or result.score > best.score:
                best = result
        except Exception:
            continue

    if best and best.entries:
        return best
    return ParseResult(strategy="none", entries=[], score=0.0, stats={"count": 0})
