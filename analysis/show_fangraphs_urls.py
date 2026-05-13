"""
Show the FanGraphs URLs that pybaseball constructs for the three data fetches
this project uses: pitcher stats, team batting, and team bullpen (relievers).

Monkey-patches fetch_url so no actual HTTP request is made.
"""

from urllib.parse import urlencode

import pybaseball.datasources.html_table_processor as _html_tp


class _StopAfterCapture(BaseException):
    pass


def _capture_url(url: str, params: dict[str, object] | None = None) -> bytes:
    full = f"{url}?{urlencode(params)}" if params else url
    # BaseException bypasses the 'except Exception' handlers in data_retrieval.py
    raise _StopAfterCapture(full)


# Patch fetch_url in the module that actually calls it (html_table_processor
# imports it by name, so we must patch it there, not in http_fetcher).
_html_tp.fetch_url = _capture_url

# Import after the patch so the patched fetch_url is in place when pybaseball
# module-level singletons are created.
from mlb_watchability.data_retrieval import (  # noqa: E402
    get_all_pitcher_stats,
    get_all_team_bullpen_stats,
    get_all_team_stats,
)

SEASON = 2026
CALLS = [
    ("pitcher stats", lambda: get_all_pitcher_stats(SEASON)),
    ("team batting", lambda: get_all_team_stats(SEASON)),
    ("team bullpen/relievers", lambda: get_all_team_bullpen_stats(SEASON)),
]

for label, fn in CALLS:
    try:
        fn()  # type: ignore[no-untyped-call]
    except _StopAfterCapture as exc:
        print(f"# {label}")
        print(exc)
        print()
    except Exception as exc:
        print(f"# {label}: unexpected error — {exc}\n")
