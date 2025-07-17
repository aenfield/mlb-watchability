# Architecture Specification – MLB Watchability, v0.1

This is the main pre-implementation summary for the first cut at this experimental project.

NOTE: I had o3 and Sonnet 4 generate their own takes on architecture.md files using vision-and-reqs.md as input. They both seemed decent - at least based on little experience as I'm trying out this kind of workflow for the first time - but I preferred the o3 output marginally more due to its somewhat broader consideration of things like CI/CD and slightly more concise output (at least on its face). So I went with the o3 file, which is the majority of this document, and then made some relatively minor changes/updates. (The original o3 and Sonnet 4 outputs are in the source-archive subdirectory.)

## 1. Overview

MLB Watchability is a Python‑based system that ranks every Major League Baseball game on a given day by an overall “Game NERD” (gNERD) score so fans can quickly decide which match‑ups are the most entertaining to watch or listen to. A daily job gathers the minimal statistics needed, computes pitcher (pNERD), team (tNERD), and game (gNERD) scores, and exposes them via a CLI today (with room to grow into an API or web UI).

## 2. System design

NOTE: These actually came from the Sonnet 4 output, which I liked a bit better than the o3 architecture.

### High-level architecture

```mermaid
graph TD
    A[Console Application] --> B[Game Score Calculator]
    A --> C[Data Retrieval Module]
    C --> D[pybaseball Library]
    D --> E[External Baseball APIs]
    B --> F[pNERD Calculator]
    B --> G[tNERD Calculator]
    F --> H[Pitcher Statistics]
    G --> I[Team Statistics]
    C --> H
    C --> I
    A --> J[JSON Output]
    A --> K[Console Output]
```

### Data flow

```mermaid
sequenceDiagram
    participant CLI as Console App
    participant DataRetrieval as Data Retrieval Module
    participant Calculator as Game Score Calculator
    participant PyBaseball as pybaseball Library

    CLI->>DataRetrieval: Request game data for date
    DataRetrieval->>PyBaseball: Get games for date
    PyBaseball-->>DataRetrieval: Game list with teams, pitchers, times

    CLI->>DataRetrieval: Request pitcher statistics
    DataRetrieval->>PyBaseball: Get pitcher stats for starting pitchers
    PyBaseball-->>DataRetrieval: Pitcher statistics

    CLI->>DataRetrieval: Request team statistics
    DataRetrieval->>PyBaseball: Get team stats
    PyBaseball-->>DataRetrieval: Team statistics

    CLI->>Calculator: Calculate gNERD scores
    Calculator->>Calculator: Calculate pNERD for each pitcher
    Calculator->>Calculator: Calculate tNERD for each team
    Calculator->>Calculator: Calculate gNERD for each game
    Calculator-->>CLI: JSON array with scores

    CLI->>CLI: Output results to console
```

## 3. Tech‑stack recommendations

| Layer                        | Choice                       | Rationale                                                                                               |
| ---------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------- |
| Language                     | Python ≥ 3.12                | Matches constraint to use “recent Python”; strong data-science ecosystem.                               |
| Dependency mgr               | UV                           | Ultrafast resolver; single tool for venv + lock; aligns with requirement.                               |
| Data access                  | pybaseball                   | Provides Statcast, FanGraphs, and Baseball-Reference endpoints with one API; already suggested.         |
| CLI framework                | Typer                        | Modern, type-safe CLI over Click; easy testing.                                                         |
| DataFrame                    | Polars (or Pandas)           | Columnar, fast, zero-copy; simplifies z-score & vector math.                                            |
| Testing                      | pytest + pytest-mock         | De-facto standard, rich fixtures; mock network calls.                                                   |
| CI/CD                        | GitHub Actions               | Native to repo; schedule workflows; free minutes.                                                       |
| Packaging                    | PEP 621 + pyproject.toml     | Declarative; works with UV.                                                                             |
| Optional persistence         | SQLite (duckdb for columnar) | Zero-config; store historical scores if desired.                                                        |
| Additional development tools | ruff, mypy                   | Code formatting with AND fast linting and code quality checks with ruff, static type-checking with mypy |

## 4. High‑level modules / services

| Module                | Responsibilities                                                                                                    |
| --------------------- | ------------------------------------------------------------------------------------------------------------------- |
| console_application   | Main CLI entry point using Typer; parse date flag, orchestrate data retrieval and scoring, handle output.           |
| data_retrieval_module | Centralized data access layer; coordinates calls to pybaseball for games, pitcher stats, and team stats.            |
| game_score_calculator | Core scoring engine; orchestrates pNERD and tNERD calculations to produce final gNERD scores.                       |
| pnerd_calculator      | Pitcher-specific statistics calculator; computes z-scores and applies pNERD formula with caps and positive rules.   |
| tnerd_calculator      | Team-specific statistics calculator; computes z-scores and applies tNERD formula with caps and positive rules.      |
| pitcher_statistics    | Data structures and validation for pitcher statistical data required for pNERD calculations.                        |
| team_statistics       | Data structures and validation for team statistical data required for tNERD calculations.                           |
| json_output           | JSON formatting module; structures game scores as JSON for programmatic consumption.                                |
| console_output        | Console formatting module; creates human-readable tables and displays for terminal output.                          |
| tests/                | Unit tests (calculator with fixed fixtures) and integration tests (network calls mocked or live, behind `-m live`). |
| scheduler (optional)  | GitHub Actions workflow or cron to run daily and push artefact/site.                                                |

## 5. Data storage / access

- Ephemeral in memory for v0.1 – statistics loaded into DataFrames → calculations → discard.
- Optional local DB (SQLite / DuckDB) to cache raw pulls & computed scores for historical visualisation or re-runs.
- Use simple repository pattern (`repo.py`) to abstract reads so swapping storage is non-breaking.

## 6. Infrastructure & deployment

| Environment          | Details                                                                                                              |
| -------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Local dev            | `uv install` → `uv run mlb-watchability-cli --date 2025-07-04`.                                                      |
| CI pipeline          | GitHub Actions: matrix on OS / Python; `uv pip sync`, run tests, build wheel.                                        |
| Daily job            | Scheduled workflow (or AWS Lambda with EventBridge) calls CLI, commits `scores-YYYY-MM-DD.json` to `gh-pages` or S3. |
| Container (optional) | Distroless image with CPython, UV, app code; used for Lambda or K8s CronJob.                                         |

## 7. Security & compliance

- Read-only public data – no PII; low risk.
- Lock dependency versions; enable Dependabot.
- Add GitHub OIDC secrets if future paid APIs are used.
- Enforce `--require-hashes` in UV to prevent supply-chain attacks.
- Use Bandit and ruff in CI for static analysis.
- Follow MIT License compatibility for `pybaseball` and FanGraphs terms of use.

## 8. Open questions & assumptions

- Do we need to store historical gNERD scores for trend analytics or publish only current day?
- Should the constant terms (3.8, 4.0) be configurable via YAML?
- Rate limits of pybaseball endpoints—do we require local caching layer?
- Target users beyond CLI—REST API? web front-end?
- How to handle double-headers and opener/bullpen games where starters are unknown?

## 9. Future considerations

- Web UI – React/Next.js site fed from JSON artefacts; sortable tables, charts.
- Notification Bot – Slack/Discord bot that posts top-5 watchable games daily.
- Historical analytics – store multi-season gNERD scores to validate metric predictive value.
- Parallel data pulls – switch to `httpx` + async for faster retrieval.
- Containerised microservice – expose `/games?date=` endpoint; scale with Kubernetes HPA on opening week traffic.
- ML enhancements – train model to predict “watchability” using additional inputs (e.g. playoff impact, rivalry flag).

```

```
