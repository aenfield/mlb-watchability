# MLB Watchability - TODO List

This TODO list drives the implementation of the MLB Watchability project, following test-driven development (TDD) principles and progressive complexity. Items are ordered so that something is runnable from the early stages and functionality is progressively added.

Foundation & Setup

1. ~~Set up project structure with pyproject.toml configuration for UV, dependencies (typer, pybaseball, polars/pandas, pytest, ruff, mypy, black), and entry point~~

2. ~~Create basic CLI entry point with Typer that accepts date parameter and prints 'Hello World'~~

3. ~~Set up basic GitHub Actions CI/CD workflow that runs tests, ruff linting, and mypy type checking~~

Core Implementation

4. Create basic data retrieval module that can fetch game schedule for a given date using pybaseball

5. Write integration tests for data retrieval module with mocked pybaseball calls

6. Connect CLI application to data retrieval module to fetch real game data

7. Create data structures for pitcher statistics (xFIP-, SwStrk, Strk, Velo, Age, Pace, Luck, KN) with validation

8. Write unit tests for pitcher statistics data structures with hardcoded test data

9. Expand data retrieval module to fetch pitcher statistics for starting pitchers using pybaseball

10. Write integration tests for pitcher statistics retrieval with mocked pybaseball calls

11. Create data structures for team statistics (Bat, HR%, BsR, Bull, Def, Pay, Age, Luck) with validation

12. Write unit tests for team statistics data structures with hardcoded test data

13. Expand data retrieval module to fetch team statistics using pybaseball

14. Write integration tests for team statistics retrieval with mocked pybaseball calls

15. Implement pNERD calculator with z-score calculations, caps, and positive-only rules

16. Write comprehensive unit tests for pNERD calculator with known inputs and expected outputs

17. Implement tNERD calculator with z-score calculations, caps, and positive-only rules

18. Write comprehensive unit tests for tNERD calculator with known inputs and expected outputs

19. Create game score calculator that orchestrates pNERD and tNERD calculations to produce gNERD scores

20. Write unit tests for game score calculator with hardcoded pitcher and team data

21. Implement JSON output formatter that structures game scores according to specified format

22. Write unit tests for JSON output formatter with expected output structure

23. Implement console output formatter for human-readable terminal display

24. Write unit tests for console output formatter with expected display format

Integration & Enhancement

25. Connect CLI application to game score calculator to process retrieved data

26. Connect CLI application to output formatters to display results

27. Add end-to-end integration tests for complete workflow from date input to score output

28. Review error handling for missing data, API failures, and edge cases throughout the application, and add/augment where useful

29. Check for need for additional tests to improve error handling - for example, missing pitchers, API timeouts, invalid dates

30. Add retry logic for pybaseball API calls

31. Enhance comprehensive logging throughout the application for debugging and monitoring

32. Create comprehensive documentation with usage examples and API reference

## Additional TODO possibilities, depending on need

- Add rate limiting for pybaseball calls.
- Optimize data retrieval to minimize API calls and improve performance

## Implementation Notes

These are derived from the architecture.md and vision-and-reqs.md files.

- Follow TDD principles: write tests before implementation
- Use UV for dependency management (not pip)
- Apply sentence case for all titles and important text
- Reference specs in the `specs/` directory (but do not use content in the `specs/source-archive/` sub-directory)
- Handle missing data gracefully with appropriate defaults or errors
- Respect rate limits when calling external APIs through pybaseball
- Application should be stateless - no data persistence between runs
