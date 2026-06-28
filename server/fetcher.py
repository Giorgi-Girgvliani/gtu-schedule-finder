from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

import httpx

from .config import CACHE_DIR, CACHE_TTL_SECONDS, LOCAL_PDF_DIR

CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _encode_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme and parts.netloc:
        path = quote(parts.path, safe="/:%")
        return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))
    return url


def _cache_path(url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    suffix = ".pdf" if url.lower().split("?")[0].endswith(".pdf") else ".html"
    return CACHE_DIR / f"{digest}{suffix}"


def fetch_url(url: str, *, force: bool = False) -> bytes:
    path = _cache_path(url)
    if not force and path.exists():
        age = time.time() - path.stat().st_mtime
        if age < CACHE_TTL_SECONDS:
            return path.read_bytes()

    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        response = client.get(_encode_url(url))
        response.raise_for_status()
        content = response.content

    path.write_bytes(content)
    return content


def fetch_local_or_remote(url: str, local_path: Path | None = None) -> bytes:
    if local_path and local_path.exists():
        return local_path.read_bytes()
    return fetch_url(url)
