from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import STATIC_DIR
from .search import load_schedule, search_by_lecturer, suggest_teachers

app = FastAPI(
    title="GTU Schedule Finder",
    description="Search GTU timetables by lecturer name — data fetched live from leqtori.gtu.ge",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    index = load_schedule()
    weekly = sum(1 for e in index.entries if e.schedule_type == "weekly")
    exams = sum(1 for e in index.entries if e.schedule_type == "exam")
    return {
        "teachers": len(index.teachers),
        "entries": len(index.entries),
        "weekly_entries": weekly,
        "exam_entries": exams,
        "sources": index.sources,
        "errors": index.errors,
        "loaded_at": index.loaded_at,
    }


@app.post("/api/refresh")
def refresh():
    index = load_schedule(force=True)
    return {
        "entries": len(index.entries),
        "teachers": len(index.teachers),
        "errors": index.errors,
    }


@app.get("/api/search")
def search(
    q: str = Query(..., min_length=1, description="Lecturer name (Georgian, English, or partial)"),
    exams: bool = Query(True, description="Include final exam schedule"),
    weekly: bool = Query(True, description="Include weekly timetable"),
):
    results = search_by_lecturer(q, include_exams=exams, include_weekly=weekly)
    return {
        "query": q,
        "count": len(results),
        "results": results,
    }


@app.get("/api/teachers")
def teachers(q: str = Query("", description="Optional filter")):
    return {"teachers": suggest_teachers(q, limit=25)}


static_path = Path(STATIC_DIR)
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
def index_page():
    index_file = static_path / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "GTU Schedule Finder API. Open /static/index.html or use /api/search?q=..."}
