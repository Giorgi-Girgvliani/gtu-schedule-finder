from __future__ import annotations

from datetime import datetime, timedelta, timezone

# Georgia Standard Time (UTC+4, no DST)
TBILISI = timezone(timedelta(hours=4))

# GTU publishes next week's timetable on Saturdays (per leqtori.gtu.ge notice)
REFRESH_WEEKDAY = 5  # Saturday
# Assume new files appear during Saturday daytime — refresh after this hour (Tbilisi)
REFRESH_HOUR = 14  # 2:00 PM

# How long (seconds) to wait after startup before triggering a background
# Saturday refresh.  Gives the Render free-tier instance time to finish
# booting and start serving the cached data before hitting GTU's servers.
REFRESH_DELAY_SECONDS = 60


def last_publish_cutoff(now: datetime | None = None) -> datetime:
    """Most recent Saturday 14:00 Tbilisi — when we treat the new week as available."""
    now = now or datetime.now(TBILISI)
    days_since = (now.weekday() - REFRESH_WEEKDAY) % 7
    cutoff = (now - timedelta(days=days_since)).replace(
        hour=REFRESH_HOUR, minute=0, second=0, microsecond=0
    )
    if now < cutoff and days_since == 0:
        # Before Saturday 14:00 — previous week's cutoff was last Saturday
        cutoff -= timedelta(days=7)
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
