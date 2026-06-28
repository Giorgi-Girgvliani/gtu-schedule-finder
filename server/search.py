from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from .config import FALLBACK_EXAM_PDF_URLS, FALLBACK_TEACHERS_URLS, LOCAL_PDF_DIR
from .discover import discover_sources
from .fetcher import fetch_url
from .html_parser import ScheduleEntry, list_teachers, parse_teachers_html
from .pdf_parser import parse_exam_pdf
from .schedule_refresh import format_loaded_at, should_refresh_weekly
from .storage import load_index, save_index
from .translator import name_matches, normalize_name, translate_course_line


@dataclass
class ScheduleIndex:
    entries: list[ScheduleEntry] = field(default_factory=list)
    teachers: list[str] = field(default_factory=list)
    loaded_at: float = 0.0
    sources: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


_index: ScheduleIndex | None = None
_loading = False
_load_lock = threading.Lock()


def _index_from_storage() -> ScheduleIndex | None:
    stored = load_index()
    if not stored:
        return None
    entries, teachers, loaded_at, sources, errors = stored
    if not entries:
        return None
    return ScheduleIndex(
        entries=entries,
        teachers=teachers,
        loaded_at=loaded_at,
        sources=sources,
        errors=errors,
    )


def _status_payload(index: ScheduleIndex, *, ready: bool, loading: bool, message: str, updating: bool = False) -> dict:
    weekly = sum(1 for e in index.entries if e.schedule_type == "weekly")
    exams = sum(1 for e in index.entries if e.schedule_type == "exam")
    return {
        "ready": ready,
        "loading": loading,
        "updating": updating,
        "message": message,
        "teachers": len(index.teachers),
        "entries": len(index.entries),
        "weekly_entries": weekly,
        "exam_entries": exams,
        "sources": index.sources,
        "errors": index.errors,
        "loaded_at": index.loaded_at,
        "last_updated": format_loaded_at(index.loaded_at),
    }


def get_status() -> dict:
    global _index

    if _loading:
        if _index and _index.entries:
            return _status_payload(
                _index,
                ready=True,
                loading=True,
                updating=True,
                message="New timetable is on the way — downloading from GTU now. You can still search the previous data.",
            )
        return {
            "ready": False,
            "loading": True,
            "updating": False,
            "message": "First-time setup — downloading and parsing GTU timetables (~30 seconds)…",
        }

    if not _index or not _index.entries:
        return {
            "ready": False,
            "loading": False,
            "updating": False,
            "message": "Schedule data not loaded yet.",
        }

    if should_refresh_weekly(_index.loaded_at):
        start_background_load(force=True)
        return _status_payload(
            _index,
            ready=True,
            loading=True,
            updating=True,
            message="GTU updates timetables every Saturday — fetching the new week now. You can still search last week's data.",
        )

    return _status_payload(
        _index,
        ready=True,
        loading=False,
        message="Ready",
    )


def has_searchable_data() -> bool:
    return bool(_index and _index.entries)


def start_background_load(*, force: bool = False) -> None:
    if _loading:
        return
    if not force and _index and not should_refresh_weekly(_index.loaded_at):
        return

    thread = threading.Thread(target=lambda: load_schedule(force=force), daemon=True)
    thread.start()


def bootstrap() -> None:
    """Load saved data on startup; refresh in background only if a Saturday has passed."""
    global _index
    stored = _index_from_storage()
    if stored:
        _index = stored
        if should_refresh_weekly(stored.loaded_at):
            start_background_load(force=True)
    else:
        start_background_load(force=True)


def load_schedule(*, force: bool = False) -> ScheduleIndex:
    global _index, _loading

    if not force and _index and not should_refresh_weekly(_index.loaded_at):
        return _index

    with _load_lock:
        if not force and _index and not should_refresh_weekly(_index.loaded_at):
            return _index

        _loading = True
        try:
            index = _build_index(force=force)
            _index = index
            save_index(index.entries, index.teachers, index.loaded_at, index.sources, index.errors)
            return index
        finally:
            _loading = False


def _build_index(*, force: bool = False) -> ScheduleIndex:
    index = ScheduleIndex(loaded_at=time.time())

    teacher_urls, exam_pdfs = discover_sources()
    if not teacher_urls:
        teacher_urls = FALLBACK_TEACHERS_URLS
    if not exam_pdfs:
        exam_pdfs = FALLBACK_EXAM_PDF_URLS

    for url in teacher_urls:
        try:
            html = fetch_url(url, force=force)
            index.entries.extend(parse_teachers_html(html, url))
            index.teachers.extend(list_teachers(html))
            index.sources.append(url)
        except Exception as exc:
            index.errors.append(f"Weekly timetable failed ({url}): {exc}")

    for faculty, url in exam_pdfs:
        try:
            pdf = fetch_url(url, force=force)
            index.entries.extend(parse_exam_pdf(pdf, faculty, url))
            index.sources.append(url)
        except Exception as exc:
            index.errors.append(f"Exam PDF failed ({faculty}): {exc}")

    if LOCAL_PDF_DIR.exists():
        for pdf_path in sorted(LOCAL_PDF_DIR.glob("*.pdf")):
            try:
                pdf = pdf_path.read_bytes()
                faculty = pdf_path.stem.replace("_", " ")
                index.entries.extend(parse_exam_pdf(pdf, faculty, f"local:{pdf_path.name}"))
                index.sources.append(f"local:{pdf_path.name}")
            except Exception as exc:
                index.errors.append(f"Local PDF failed ({pdf_path.name}): {exc}")

    seen: set[str] = set()
    unique_teachers: list[str] = []
    for name in index.teachers:
        key = normalize_name(name)
        if key not in seen:
            seen.add(key)
            unique_teachers.append(name)

    for entry in index.entries:
        if entry.schedule_type != "exam":
            continue
        key = normalize_name(entry.teacher_original)
        if key and key not in seen:
            seen.add(key)
            unique_teachers.append(entry.teacher_original)

    index.teachers = sorted(unique_teachers, key=normalize_name)
    return index


def search_by_lecturer(query: str, *, include_exams: bool = True, include_weekly: bool = True) -> list[dict]:
    if not has_searchable_data():
        load_schedule()
    query = query.strip()
    if not query or not _index:
        return []

    results: list[ScheduleEntry] = []
    for entry in _index.entries:
        if entry.schedule_type == "exam" and not include_exams:
            continue
        if entry.schedule_type == "weekly" and not include_weekly:
            continue
        if name_matches(entry.teacher_original, query):
            results.append(entry)

    def sort_key(item: ScheduleEntry) -> tuple:
        if item.schedule_type == "exam":
            return (0, item.date, item.time, item.course)
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_idx = day_order.index(item.day) if item.day in day_order else 99
        return (1, day_idx, item.time, item.course)

    results.sort(key=sort_key)

    output: list[dict] = []
    for entry in results:
        data = entry.to_dict()
        data["teacher"] = entry.teacher_original
        data["course"] = translate_course_line(entry.course_original)
        if entry.schedule_type == "exam":
            data["day"] = entry.date
        output.append(data)

    return output


def suggest_teachers(query: str, limit: int = 10) -> list[str]:
    if not has_searchable_data():
        return []
    assert _index is not None
    query = normalize_name(query)
    if not query:
        return _index.teachers[:limit]
    return [name for name in _index.teachers if name_matches(name, query)][:limit]
