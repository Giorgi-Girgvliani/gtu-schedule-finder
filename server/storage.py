from __future__ import annotations

import json
from pathlib import Path

from .config import DATA_DIR
from .html_parser import ScheduleEntry

INDEX_FILE = DATA_DIR / "schedule-index.json"


def save_index(
    entries: list[ScheduleEntry],
    teachers: list[str],
    loaded_at: float,
    sources: list[str],
    errors: list[str],
) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "loaded_at": loaded_at,
        "teachers": teachers,
        "sources": sources,
        "errors": errors,
        "entries": [entry.to_dict() for entry in entries],
    }
    INDEX_FILE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_index() -> tuple[list[ScheduleEntry], list[str], float, list[str], list[str]] | None:
    if not INDEX_FILE.exists():
        return None
    try:
        payload = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        entries = [ScheduleEntry(**item) for item in payload.get("entries", [])]
        return (
            entries,
            payload.get("teachers", []),
            float(payload.get("loaded_at", 0)),
            payload.get("sources", []),
            payload.get("errors", []),
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
