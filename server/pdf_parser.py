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


HEADER_HINT_RE = re.compile(r"ჯგუფ|კურს|გვარ|პროფ|თარიღ|აუდიტ|დრო|date|teacher|group", re.I)
ROOM_RE = re.compile(r"\b\d{1,3}\s*[-–]\s*\d{1,3}|корпус|этаж|building|აუდიტ|კორპუს")
TIME_ONLY_RE = re.compile(r"^\D*\d{1,2}:\d{2}\D*$")


def _row_is_header(cells: list[str]) -> bool:
    joined = " ".join(cells)
    return len(HEADER_HINT_RE.findall(joined)) >= 2


def _is_groupish(cell: str) -> bool:
    return bool(GROUP_RE.match(cell.strip()))


def _looks_like_date(cell: str) -> bool:
    if DATE_NUMERIC.search(cell):
        return True
    return any(m in cell for m in GEORGIAN_MONTHS) and bool(re.search(r"\d", cell))


def _infer_columns(rows: list[list[str]]) -> dict[str, int]:
    """Infer column roles from cell *content*, independent of column order.

    GTU exam PDFs vary the column order and language between faculties (and
    sometimes within one PDF). Instead of trusting header text or a fixed
    layout, we score every column by how often its cells look like a date,
    a time, a group number, a room, or a person name, then assign each role
    to its best-fitting column.
    """
    if not rows:
        return {}
    ncols = max(len(r) for r in rows)
    score = {k: [0] * ncols for k in ("date", "time", "group", "room", "person", "text")}

    for row in rows:
        for i in range(ncols):
            cell = row[i].strip() if i < len(row) else ""
            if not cell:
                continue
            if _looks_like_date(cell):
                score["date"][i] += 1
            elif TIME_ONLY_RE.match(cell):
                score["time"][i] += 1
            if _is_groupish(cell):
                score["group"][i] += 1
            if ROOM_RE.search(cell):
                score["room"][i] += 1
            if is_likely_person_name(cell):
                score["person"][i] += 1
            if re.search(r"[^\W\d_]{3,}", cell, re.UNICODE):
                score["text"][i] += 1

    used: set[int] = set()

    def take(key: str, *, avoid_text: bool = False) -> int | None:
        best, best_val = None, 0
        for i in range(ncols):
            if i in used:
                continue
            val = score[key][i]
            if val > best_val:
                best, best_val = i, val
        if best is not None and best_val > 0:
            used.add(best)
        return best

    cols: dict[str, int] = {}
    for key in ("date", "time", "group", "room", "person"):
        idx = take(key)
        if idx is not None:
            cols[key] = idx
    if "person" in cols:
        cols["teacher"] = cols.pop("person")

    # Course = the remaining free-text column with the most text (excluding
    # the columns already claimed by structured roles / the teacher).
    best, best_val = None, 0
    for i in range(ncols):
        if i in used:
            continue
        if score["text"][i] > best_val:
            best, best_val = i, score["text"][i]
    if best is not None:
        cols["course"] = best
    return cols


def _carry_entry(
    row: list[str],
    cols: dict[str, int],
    *,
    faculty: str,
    source_url: str,
    state: dict,
) -> ScheduleEntry | None:
    def cell(key: str) -> str:
        idx = cols.get(key, -1)
        if idx < 0 or idx >= len(row):
            return ""
        return _clean_cell(row[idx])

    group = cell("group")
    if group and GROUP_RE.match(group):
        state["group"] = group
    group = state.get("group", "")

    course = cell("course")
    teacher_raw = normalize_person_name(cell("teacher"))
    date = _parse_georgian_date(cell("date"))
    time = _extract_time(cell("time")) or _extract_time(cell("date"))
    room = cell("room")

    # A row with only a professor (and no course/date) is a co-examiner of the
    # previous exam — reuse the previous course/date/time/room for it.
    if teacher_raw and not course and not date:
        course = state.get("course", "")
        date = date or state.get("date", "")
        time = time or state.get("time", "")
        room = room or state.get("room", "")
    else:
        if course:
            state["course"] = course
        if date:
            state["date"] = date
        if time:
            state["time"] = time
        if room:
            state["room"] = room

    if not course:
        return None

    teacher = teacher_raw if is_likely_person_name(teacher_raw) else ""

    return ScheduleEntry(
        teacher=teacher,
        teacher_original=teacher,
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
    )


def parse_tables(pdf_bytes: bytes, faculty: str, source_url: str) -> list[ScheduleEntry]:
    # 1) Collect every data row across all pages (headers/blank rows dropped).
    raw_rows: list[list[str]] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table or []:
                    cells = [_clean_cell(c) for c in row]
                    if not any(cells):
                        continue
                    if _row_is_header(cells):
                        continue
                    raw_rows.append(cells)

    if not raw_rows:
        return []

    # 2) Infer the column layout once from the whole document.
    cols = _infer_columns(raw_rows)
    if "course" not in cols and "teacher" not in cols:
        return []

    # 3) Build entries, carrying group / co-examiner context forward.
    entries: list[ScheduleEntry] = []
    state: dict = {}
    for row in raw_rows:
        entry = _carry_entry(row, cols, faculty=faculty, source_url=source_url, state=state)
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
