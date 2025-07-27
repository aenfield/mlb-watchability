# CLAUDE.md

## Project overview

MLB Watchability is a Python command-line application that calculates "Game NERD scores" (gNERD) for MLB games to help users identify the most watchable games on any given day. The system combines pitcher-specific statistics (pNERD) and team-specific statistics (tNERD) to generate an overall watchability score for each game.

## Development commands

To see how to run tests, lint, install dependencies, etc, use @README.md .

## Architecture

Retrieve the architecture from @specs/architecture.md. This might be older than the actual implementation, so check the code too and prefer what you learn from the code.

## Key statistics and calculations

Retrieve details for statistic calculations - pNERD, tNERD, gNERD - from specs/@vision-and-reqs.md .

## Technology stack

Retrieve technology stack information from architecture.md.

## Testing strategy

- **Unit tests**: Test calculation modules with static, hardcoded input data
- **Integration tests**: Validate data retrieval from external sources
- **CI/CD**: GitHub Actions workflow for automated testing using the chosen Python version

Additional testing information is in architecture.md.

## Development and additional notes

- The project uses UV for dependency management - always use `uv` commands instead of `pip`.
- Data is not persisted between runs - the application is stateless.
- Statistical formulas are complex and specific - refer to the original FanGraphs methodology as documented in specs/vision-and-reqs.md.
- Also don't forget to consider the information in specs/architecture.md.
- Handle missing data gracefully with appropriate defaults or errors.
- Respect rate limits when calling external APIs through pybaseball.
- All titles and bolded/important text in specs and UI should be sentence case.
- When using the specs and documentation as context - which you should do almost always - use the files in the specs/ directory, and ignore the files in the source-archive directory (becaus that directory holds older content that has been superceded or incorporated into the actualy files in the root specs/ directory)
- Don't mark off items in todo.md unless I specifically tell you to do that.
- You can use ./run-all-checks.sh to double-check that everything is good before a commit - i.e., black, ruff, mypy, tests.
- If you add new tests, run them then and there so you can more easily fix issues surfaced by the tests before you do other things.
- For testing numbers and in the implementation being tested, there's no need to do numeric validation of data from external sources - for example, if a snapshot of data from pybaseball has 'fielding runs' between -35 and 35, there's no need to add a test that checks that this is the case in current or future data and there's no need to add actual implementation code - like in the team_stats impl - to validate that fielding runs data is in this range. At the same time, do validate our own calculations - if we calculate a new field based on existing data, we should have a test or tests to make sure that the new calculation we've implemented is correct.
- There's also no need to validate that z-scores are within a particular range, as long as we validate that the z-score calculation we implement itself is correct.
- We don't need this to work with historical data before this year, so you don't need to test with 2024 or earlier - just use 2025 or later if it's no longer 2025. This is specifically and also the case when double-checking with the mlbw command line tool - i.e., do not run 'uv run mlbw 2024-10-10' - instead, asssuming it's 2025, run something like 'uv run mlbw 2025-05-15'.
