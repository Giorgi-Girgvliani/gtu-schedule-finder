from __future__ import annotations

from datetime import datetime, timedelta, timezone

# Georgia Standard Time (UTC+4, no DST)
TBILISI = timezone(timedelta(hours=4))

# GTU publishes next week's timetable on Saturdays (per leqtori.gtu.ge notice)
REFRESH_WEEKDAY = 5  # Saturday


def last_publish_cutoff(now: datetime | None = None) -> datetime:
    """Start of the most recent Saturday in Tbilisi time."""
    now = now or datetime.now(TBILISI)
    days_since = (now.weekday() - REFRESH_WEEKDAY) % 7
    cutoff = (now - timedelta(days=days_since)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return cutoff


def should_refresh_weekly(loaded_at: float) -> bool:
    if not loaded_at:
        return True
    loaded = datetime.fromtimestamp(loaded_at, TBILISI)
    return loaded < last_publish_cutoff()


def format_loaded_at(loaded_at: float) -> str:
    if not loaded_at:
        return "Never"
    return datetime.fromtimestamp(loaded_at, TBILISI).strftime("%A %d %b %Y, %H:%M (%Z)")
