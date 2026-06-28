from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any

from bs4 import BeautifulSoup

from .config import DAY_MAP


@dataclass
class ScheduleEntry:
    teacher: str
    teacher_original: str
    course: str
    course_original: str
    day: str
    time: str
    room: str
    group: str
    source: str
    schedule_type: str  # "weekly" or "exam"
    faculty: str = ""
    date: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_day(header: str) -> str:
    header = header or ""
    match = re.search(r"/\s*([A-Za-z.]+)", header)
    if match:
        key = match.group(1).lower().rstrip(".")
        return DAY_MAP.get(key, match.group(1))
    return header.strip()


def _parse_time(slot: str) -> str:
    match = re.search(r"(\d{1,2}:\d{2})", slot or "")
    return match.group(1) if match else (slot or "").strip()


def _parse_cell(raw_html: str) -> tuple[str, str, str]:
    text = BeautifulSoup(raw_html, "lxml").get_text("\n", strip=True)
    if not text or text == "---":
        return "", "", ""

    parts = [p.strip() for p in text.split("\n") if p.strip()]
    group = parts[0] if parts else ""
    course = parts[1] if len(parts) > 1 else ""
    room = parts[-1] if len(parts) > 2 else (parts[2] if len(parts) > 2 else "")
    if len(parts) == 2:
        room = parts[1]
        course = parts[0]
        group = ""
    return group, course, room


def _build_grid(table) -> list[list[str | None]]:
    rows = table.find("tbody").find_all("tr")
    grid: list[list[str | None]] = []
    span_tracker: dict[tuple[int, int], tuple[str, int]] = {}

    for row_idx, row in enumerate(rows):
        while len(grid) <= row_idx:
            grid.append([])

        col_idx = 0
        for cell in row.find_all(["td", "th"], recursive=False):
            while col_idx < len(grid[row_idx]) and grid[row_idx][col_idx] is not None:
                col_idx += 1

            if (row_idx, col_idx) in span_tracker:
                content, remaining = span_tracker[(row_idx, col_idx)]
                grid[row_idx].append(content)
                if remaining > 1:
                    span_tracker[(row_idx + 1, col_idx)] = (content, remaining - 1)
                del span_tracker[(row_idx, col_idx)]
                col_idx += 1
                continue

            content = cell.decode_contents().strip()
            colspan = int(cell.get("colspan", 1))
            rowspan = int(cell.get("rowspan", 1))

            for _ in range(colspan):
                grid[row_idx].append(content if _ == 0 else None)
                if rowspan > 1:
                    span_tracker[(row_idx + 1, col_idx)] = (content, rowspan - 1)
                col_idx += 1

    return grid


def parse_teachers_html(html: bytes, source_url: str) -> list[ScheduleEntry]:
    soup = BeautifulSoup(html, "lxml")
    entries: list[ScheduleEntry] = []

    for table in soup.find_all("table", id=re.compile(r"^table_\d+$")):
        header_row = table.find("thead")
        if not header_row:
            continue

        teacher_th = header_row.find("th", attrs={"colspan": True})
        teacher_name = teacher_th.get_text(" ", strip=True) if teacher_th else "Unknown"

        day_headers = header_row.find_all("th", class_="xAxis")
        days = [_parse_day(th.get_text(" ", strip=True)) for th in day_headers]

        grid = _build_grid(table)
        time_labels: list[str] = []

        for row in table.find("tbody").find_all("tr"):
            time_th = row.find("th", class_="yAxis")
            if time_th:
                time_labels.append(_parse_time(time_th.get_text(" ", strip=True)))

        for row_idx, row_cells in enumerate(grid):
            if row_idx >= len(time_labels):
                break
            time_label = time_labels[row_idx]

            for col_idx, cell_html in enumerate(row_cells):
                if col_idx >= len(days) or not cell_html or cell_html == "---":
                    continue

                group, course, room = _parse_cell(cell_html)
                if not course and not room:
                    continue

                entries.append(
                    ScheduleEntry(
                        teacher=teacher_name.strip(),
                        teacher_original=teacher_name.strip(),
                        course=course,
                        course_original=course,
                        day=days[col_idx],
                        time=time_label,
                        room=room,
                        group=group,
                        source=source_url,
                        schedule_type="weekly",
                    )
                )

    return entries


def list_teachers(html: bytes) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    names: list[str] = []
    for link in soup.select("ul li a[href^='#table_']"):
        name = link.get_text(" ", strip=True)
        if name:
            names.append(name)
    return names
