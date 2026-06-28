# GTU Schedule Finder

A simple tool for international GTU students to search timetables by lecturer name, with results shown in English. Data is fetched live from [leqtori.gtu.ge](http://leqtori.gtu.ge/).

## What it does

- Fetches **weekly timetables** from GTU's HTML schedule pages (`teachers_*.html`)
- Fetches **final exam schedules** from faculty PDF files
- Lets you search by lecturer name (Georgian, English transliteration, or partial match)
- Translates course titles to English on demand

## Quick start

```bash
cd gtu-schedule
python -m pip install -r requirements.txt
python -m uvicorn server.main:app --reload --host 127.0.0.1 --port 8000
```

Or double-click `run.bat` on Windows.

Open **http://127.0.0.1:8000** in your browser.

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/search?q=Milashvili` | Search by lecturer name |
| `GET /api/teachers?q=gra` | Autocomplete lecturer names |
| `GET /api/status` | Index stats and source URLs |
| `POST /api/refresh` | Force re-download from GTU |

Query params for search: `weekly=true`, `exams=true`.

## Weekly timetable updates

GTU publishes the next week's schedule on **Saturdays** (see leqtori.gtu.ge). This app:

- **Fetches live links** from [leqtori.gtu.ge](http://leqtori.gtu.ge/) on each reload (no manual URL edits most weeks)
- **Auto-refreshes** when data is older than the most recent Saturday (Tbilisi time)
- Shows **last updated** in the status bar

### Optional: scheduled refresh on Render

1. In Render → **Environment**, add `CRON_SECRET` = any long random string
2. On [cron-job.org](https://cron-job.org) (free), create a weekly job:
   - **URL:** `https://YOUR-APP.onrender.com/api/cron/refresh`
   - **Method:** POST
   - **Header:** `Authorization: Bearer YOUR_CRON_SECRET`
   - **Schedule:** Saturday 10:00 (Asia/Tbilisi)

This wakes the site and reloads timetables even if nobody visits.

## Updating URLs each semester

GTU changes file names on `leqtori.gtu.ge` every semester. Edit `server/config.py`:

- `TEACHERS_URLS` — weekly HTML timetable links
- `EXAM_PDF_URLS` — final exam PDF links per faculty

Copy the new links from the [leqtori.gtu.ge](http://leqtori.gtu.ge/) tab page.

## Local PDF fallback

If a PDF fails to download, drop the file into `data/pdfs/` and add a local path override in `config.py` (or replace the URL).

## Notes

- First search may take a few seconds while course names are translated.
- Timetable data is cached for 1 hour in `data/cache/`.
- Check GTU every **Saturday** for next week's schedule updates.
