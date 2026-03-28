# New season startup notes

Notes from the 2026 season startup, for reference when the 2027 season begins (around late March).

## Summary

Several things broke or degraded gracefully when the 2026 season started. Most were caused by the fact that early in a season, stats that are meaningful mid-season simply don't exist yet or are sparsely populated. The fixes are mostly in place in the code now, but some issues will recur and need manual attention each year.

---

## Issue 1: Pitcher stats crash (fixed in code)

**What happened:** The daily GitHub Actions workflow crashed immediately with:
```
RuntimeError: Failed to retrieve pitcher statistics for season 2026: 393 columns passed, passed data had 1 columns
```

**Root cause:** `pybaseball.pitching_stats(season, qual=20)` was called with `qual=20` (meaning "only return pitchers with ≥20 innings pitched"). FanGraphs returned an empty/malformed response when no pitchers had accumulated 20 IP yet (opening day/week). pybaseball tried to build a DataFrame from 393 column headers with zero data rows and crashed.

**Fix (committed):** Changed `qual=20` → `qual=1` so pybaseball always gets a valid DataFrame, then applied the `GS >= 1` and `IP >= 20` filters in Python code afterward. Pitchers who haven't yet thrown 20 IP just don't appear in the stats dict, and those games fall back to the default pNERD of 5.0.

**Expected behavior early in season:** All games will show pNERD = 5.0 (the default) for the first few weeks until enough pitchers accumulate 20 IP. This is fine and expected.

**Related:** scipy emits `SmallSampleWarning` messages (not errors) when the pitcher pool is very small (e.g. fewer than 2 pitchers). These are harmless — they appear in the logs but don't break anything.

---

## Issue 2: Team NaN gNERD scores (fixed in code)

**What happened:** After fixing the pitcher crash, 5 of 8 games showed `gNERD: nan`.

**Root cause:** `Fld` (Fielding Runs Above Average) was NaN for 22 of 24 teams in pybaseball's team batting data early in the season — FanGraphs doesn't compute meaningful fielding runs after just 1-2 games. A single NaN in `Fld` propagated through the z-score calculation to poison the entire tNERD score for every team.

Note: `Barrel%` already had NaN handling in the code; `Fld` did not.

**Fix (committed):** Added the same NaN guard for `Fld` that already existed for `Barrel%`: replace NaN with `0.0`. This is semantically correct because `Fld` is "runs above average," so 0.0 means exactly league-average fielding — a reasonable assumption when no data exists yet.

**Expected behavior early in season:** Teams will all be treated as having average fielding for the first few weeks. tNERD scores will still vary based on batting, baserunning, bullpen, payroll, age, and luck stats, which are populated earlier in the season.

---

## Issue 3: Some teams missing from pybaseball data (ongoing, not fixed)

**What happened:** 3 games showed `avg_tnerd=0.0` because their teams weren't found in pybaseball's 2026 team batting data at all (and the fallback for a missing team is 0.0).

**Teams affected (opening week 2026):** Athletics (ATH), Toronto (TOR), Colorado (COL), Miami (MIA), Kansas City (KCR), Atlanta (ATL) — these teams were absent from the pybaseball team batting results in the first days of the season.

**Status:** Not fixed — the fallback of 0.0 is acceptable for early-season gaps. These teams appeared in the data within a few days as the season got underway. Worth monitoring if it persists for more than a week.

---

## Issue 4: Team age data (manual attention needed each year)

**What happened:** Not a crash, but worth understanding. The `Age` column in `data/payroll-spotrac.2025.csv` is **not** from Spotrac — it was manually sourced from somewhere (possibly FanGraphs or Baseball Reference) and stored in the Spotrac payroll file for convenience. The commit history doesn't record the original source.

**For 2027:** Update `data/payroll-spotrac.2025.csv` (or create a new year's version) with:
- Fresh payroll data from Spotrac
- Fresh team age data — **Baseball Reference** is the recommended source: `https://www.baseball-reference.com/leagues/majors/2026-misc.shtml` (change year as needed). Use the `BatAge` column (batting roster average age, which uses age as of June 30). Note that this page may not have complete data for all 30 teams until a few weeks into the season.

The file is hardcoded in `data_retrieval.py` as `data/payroll-spotrac.2025.csv` — **update the filename and the reference in the code** when creating a new year's file.

---

## Issue 5: BLOG_REPO_TOKEN expired (manual fix required when it happens)

**What happened:** The `generate-markdown` workflow failed with "Bad credentials" when trying to check out `aenfield/blog-eleventy`. The `BLOG_REPO_TOKEN` secret had expired or been revoked.

**Fix:** Generate a new Personal Access Token (PAT) with `contents: write` access to `aenfield/blog-eleventy`, then update the `BLOG_REPO_TOKEN` secret in the `mlb-watchability` repo settings (Settings → Secrets and variables → Actions).

**For 2027:** Check PAT expiry dates when creating tokens — set them to expire after the season ends (October/November) or use a longer-lived token.

---

## General advice for season startup

1. **Trigger the workflow manually** on or just after opening day and watch the logs. Early failures are expected and most self-resolve within 1-2 weeks as stats accumulate.
2. **Update the payroll/age CSV** (`data/payroll-spotrac.YEAR.csv`) before the season starts, and update the filename reference in `data_retrieval.py`. Wait until Baseball Reference has BatAge data for all 30 teams before using it (usually a few weeks in).
3. **Check secret expiry** — the `BLOG_REPO_TOKEN` PAT needs to be valid at the start of the season.
5. **pNERD and tNERD scores will be low-quality for the first 3-4 weeks** — not enough data for meaningful z-scores. This is expected and the 5.0 defaults are reasonable stand-ins.
