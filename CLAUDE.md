# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

MLB Watchability is a Python command-line application that calculates "Game NERD scores" (gNERD) for MLB games to help users identify the most watchable games on any given day. The system combines pitcher-specific statistics (pNERD) and team-specific statistics (tNERD) to generate an overall watchability score for each game.

## Development commands

- **Run the application**: `uv run mlb-watchability-cmd`
- **Run tests**: `uv run pytest`
- **Install dependencies**: `uv sync`
- **Lint code**: `uv run ruff check`
- **Format code**: `uv run black .`
- **Type checking**: `uv run mypy .`

## Architecture

### Core modules

- **Data retrieval module** (`mlb_watchability/data_retrieval.py`): Fetches game schedules and statistical data using the pybaseball library
- **Score calculator module** (`mlb_watchability/calculator.py`): Calculates pNERD, tNERD, and gNERD scores using complex statistical formulas
- **Console application** (`mlb_watchability/cli.py`): Command-line interface orchestrating data retrieval and calculation
- **Data models** (`mlb_watchability/models.py`): Type definitions and data structures for games, pitcher stats, team stats, and scores

### Key statistics and calculations

- **pNERD (Pitcher NERD)**: Based on xFIP-, SwStrk rate, Strike rate, Velocity, Age, Pace, ERA- minus xFIP- (Luck), and Knuckleball rate
- **tNERD (Team NERD)**: Based on Park-Adjusted Batting Runs, HR%, Baserunning Runs, Bullpen xFIP, Defensive Runs, Payroll, Batter Age, and Expected vs Actual Wins
- **gNERD (Game NERD)**: Average of pNERD scores for both starting pitchers plus average of tNERD scores for both teams

## Technology stack

- **Python 3.11+**: Core language
- **UV**: Package manager and project manager (replaces pip/pipenv/poetry)
- **pybaseball**: Primary data source for MLB statistics and game information
- **pandas**: Data manipulation (included with pybaseball)
- **pytest**: Testing framework
- **pydantic**: Data validation and settings management
- **black**: Code formatting
- **ruff**: Fast linting and code quality checks
- **mypy**: Static type checking

## Data sources

The application primarily uses the pybaseball library to access:

- Game schedules and matchups
- Pitcher statistics from FanGraphs and Baseball Reference
- Team statistics from various MLB APIs

## Testing strategy

- **Unit tests**: Test calculation modules with static, hardcoded input data
- **Integration tests**: Validate data retrieval from external sources
- **CI/CD**: GitHub Actions workflow for automated testing across Python versions

## Project structure

Based on the architecture specification, the codebase should follow this structure:

```
mlb_watchability/
├── __init__.py
├── cli.py              # Console application entry point
├── data_retrieval.py   # Data fetching from pybaseball
├── calculator.py       # NERD score calculations
└── models.py           # Data structures and type definitions
```

## Development notes

- The project uses UV for dependency management - always use `uv` commands instead of `pip`
- Data is not persisted between runs - the application is stateless
- Statistical formulas are complex and specific - refer to the original FanGraphs methodology
- Handle missing data gracefully with appropriate defaults or errors
- Respect rate limits when calling external APIs through pybaseball
- All titles and bolded/important text in specs and UI should be sentence case.
