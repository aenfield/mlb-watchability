# CLAUDE.md

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

Retrieve the architecture from architecture.md.

## Key statistics and calculations

Retrieve details for statistic calculations - pNERD, tNERD, gNERD - from vision-and-reqs.md.

## Technology stack

Retrieve technology stack information from architecture.md.

## Testing strategy

- **Unit tests**: Test calculation modules with static, hardcoded input data
- **Integration tests**: Validate data retrieval from external sources
- **CI/CD**: GitHub Actions workflow for automated testing using the chosen Python version

Additional testing information is in architecture.md.

## Development notes

- The project uses UV for dependency management - always use `uv` commands instead of `pip`
- Data is not persisted between runs - the application is stateless
- Statistical formulas are complex and specific - refer to the original FanGraphs methodology as documented in vision-and-reqs.md
- Handle missing data gracefully with appropriate defaults or errors
- Respect rate limits when calling external APIs through pybaseball
- All titles and bolded/important text in specs and UI should be sentence case
- When using the specs and documentation as context - which you should do almost always - use the files in the specs/ directory, and ignore the files in the source-archive directory (becaus that directory holds older content that has been superceded or incorporated into the actualy files in the root specs/ directory)
