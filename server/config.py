from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
LOCAL_PDF_DIR = DATA_DIR / "pdfs"

GTU_PUBLIC_BASE = "http://leqtori.gtu.ge:9000/public/"
LEQTORI_PAGE_URL = "http://leqtori.gtu.ge/"

FALLBACK_TEACHERS_URLS = [
    f"{GTU_PUBLIC_BASE}teachers_2025_2026_2_15.html",
    f"{GTU_PUBLIC_BASE}prof_teachers.html",
]

FALLBACK_EXAM_PDF_URLS: list[tuple[str, str]] = []

# Minimum time between reloads within the same week (hourly cache)
CACHE_TTL_SECONDS = 3600

DAY_MAP = {
    "mon": "Monday",
    "tues": "Tuesday",
    "wed": "Wednesday",
    "thurs": "Thursday",
    "fri": "Friday",
    "sat": "Saturday",
    "sun": "Sunday",
}

LESSON_TYPE_MAP = {
    "პრაქტიკული": "Practical",
    "ლექცია": "Lecture",
    "სემინარი": "Seminar",
    "ტესტირების ცენტრი": "Testing center",
}
