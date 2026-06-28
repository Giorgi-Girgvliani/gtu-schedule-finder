from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from .config import BASE_DIR, GTU_PUBLIC_BASE, LEQTORI_PAGE_URL
from .fetcher import fetch_url

TAB_CONTENT_CANDIDATES = [
    BASE_DIR / "data" / "leqtori-tab-content.txt",
    BASE_DIR.parent / "leqtori.gtu.ge tab content.txt",
]


def _label_from_link(text: str, href: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if " / " in text:
        english = text.split(" / ", 1)[-1].strip()
        if english:
            return english
    if "Faculty" in href:
        match = re.search(r"Faculty[^_]+", unquote(href))
        if match:
            return match.group(0).replace("%20", " ").strip()
    return text or unquote(href).split("/")[-1]


def _fetch_live_page_html() -> str | None:
    try:
        return fetch_url(LEQTORI_PAGE_URL).decode("utf-8", errors="replace")
    except Exception:
        return None


def discover_sources(tab_html: str | None = None) -> tuple[list[str], list[tuple[str, str]]]:
    if tab_html is None:
        tab_html = _fetch_live_page_html()
    if tab_html is None:
        for candidate in TAB_CONTENT_CANDIDATES:
            if candidate.exists():
                tab_html = candidate.read_text(encoding="utf-8")
                break

    teacher_urls: list[str] = []
    exam_pdfs: list[tuple[str, str]] = []

    if not tab_html:
        return teacher_urls, exam_pdfs

    soup = BeautifulSoup(tab_html, "lxml")
    seen: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        if not href.startswith("http"):
            href = urljoin(GTU_PUBLIC_BASE, href)

        if href in seen:
            continue
        seen.add(href)

        lower = href.lower()
        text = link.get_text(" ", strip=True)

        if lower.endswith(".html") and ("teacher" in lower or "teachers" in lower):
            teacher_urls.append(href)
        elif lower.endswith(".pdf"):
            if "exam center" in text.lower() or "საგამოცდო ცენტრი" in text:
                continue
            if "დამატ" in text or "დამატებით" in href or "additional" in text.lower():
                continue
            if "final" in text.lower() or "გამოცდ" in text or "faculty" in lower or "school" in lower or "ფაკულტეტ" in text:
                exam_pdfs.append((_label_from_link(text, href), href))

    return teacher_urls, exam_pdfs
