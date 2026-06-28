from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import STATIC_DIR
from .search import get_status, load_schedule, search_by_lecturer, start_background_load, suggest_teachers


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_background_load()
    yield


app = FastAPI(
    title="GTU Schedule Finder",
    description="Search GTU timetables by lecturer name — data fetched live from leqtori.gtu.ge",
    version="1.0.0",
    lifespan=lifespan,
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
    return get_status()


@app.post("/api/refresh")
def refresh():
    if get_status().get("loading"):
        return {"message": "Refresh already in progress.", "loading": True}
    start_background_load(force=True)
    return {"message": "Refresh started. Data will update in about a minute.", "loading": True}


@app.post("/api/cron/refresh")
def cron_refresh(authorization: str | None = Header(default=None)):
    """Optional scheduled refresh — set CRON_SECRET on Render and call weekly via cron-job.org."""
    secret = os.environ.get("CRON_SECRET", "")
    if not secret or authorization != f"Bearer {secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    start_background_load(force=True)
    return {"ok": True, "message": "Scheduled refresh started"}


@app.get("/api/search")
def search(
    q: str = Query(..., min_length=1, description="Lecturer name (Georgian, English, or partial)"),
    exams: bool = Query(True, description="Include final exam schedule"),
    weekly: bool = Query(True, description="Include weekly timetable"),
):
    state = get_status()
    if not state.get("ready"):
        raise HTTPException(
            status_code=503,
            detail=state.get("message", "Schedule data is still loading. Please wait."),
        )
    results = search_by_lecturer(q, include_exams=exams, include_weekly=weekly)
    return {
        "query": q,
        "count": len(results),
        "results": results,
    }


@app.get("/api/teachers")
def teachers(q: str = Query("", description="Optional filter")):
    if not get_status().get("ready"):
        return {"teachers": []}
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
