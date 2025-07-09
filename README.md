# MLB Watchability

MLB Watchability is a Python command-line application that calculates "Game NERD scores" (gNERD) for MLB games to help users identify the most watchable games on any given day.

## Installation

```bash
uv sync --extra dev
```

## Usage

```bash
uv run mlb-watchability-cmd [DATE]
```

Where `DATE` is optional and should be in YYYY-MM-DD format. If not provided, defaults to today.

## Development

- **Run tests**: `uv run pytest`
- **Lint code**: `uv run ruff check`
- **Format code**: `uv run black .`
- **Type checking**: `uv run mypy .`