"""Standalone script used by the GitHub Actions Saturday-update workflow.

Run from the repository root:
    python scripts/build_index.py

It rebuilds schedule-index.json by fetching the latest timetable data from
leqtori.gtu.ge and writing the result to data/schedule-index.json so it can
be committed back to the repository.
"""

from __future__ import annotations

import sys
import os
import time

# Allow importing server.* without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from server.search import _build_index          # noqa: E402  (import after path fix)
from server.storage import INDEX_FILE, save_index  # noqa: E402


def main() -> None:
    print("Building schedule index…")
    start = time.time()

    index = _build_index(force=True)

    elapsed = time.time() - start
    print(f"Fetched and parsed in {elapsed:.1f}s")
    print(f"  Teachers : {len(index.teachers)}")
    print(f"  Entries  : {len(index.entries)} "
          f"({sum(1 for e in index.entries if e.schedule_type == 'weekly')} weekly, "
          f"{sum(1 for e in index.entries if e.schedule_type == 'exam')} exam)")
    if index.errors:
        print(f"  Warnings : {len(index.errors)}")
        for err in index.errors:
            print(f"    • {err}")
    if index.parser_log:
        print("  PDF parsers:")
        for line in index.parser_log:
            print(f"    • {line}")

    save_index(
        index.entries,
        index.teachers,
        index.loaded_at,
        index.sources,
        index.errors,
    )
    print(f"Saved → {INDEX_FILE}")


if __name__ == "__main__":
    main()
