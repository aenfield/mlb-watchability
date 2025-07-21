# MLB Watchability - TODO List

This TODO list drives the implementation of the MLB Watchability project, following test-driven development (TDD) principles and progressive complexity. Items are ordered so that something is runnable from the early stages and functionality is progressively added.

Foundation & Setup

1. ~~Set up project structure with pyproject.toml configuration for UV, dependencies (typer, pybaseball, polars/pandas, pytest, ruff, mypy, black), and entry point~~

2. ~~Create basic CLI entry point with Typer that accepts date parameter and prints 'Hello World'~~

3. ~~Set up basic GitHub Actions CI/CD workflow that runs tests, ruff linting, and mypy type checking~~

Core Implementation

4. ~~Create basic data retrieval module that can fetch game schedule for a given date, remembering to create unit tests first~~

5. ~~Write integration tests for data retrieval module with mocked pybaseball calls~~

6. ~~Connect CLI application to data retrieval module to fetch real game data~~

7. ~~Create data structures for pitcher statistics (xFIP-, SwStrk, Strk, Velo, Age, Pace, Luck, KN) with validation, using the formula in vision-and-reqs.md~~

8. ~~Write unit tests for pitcher statistics data structures with hardcoded test data~~

9. ~~Expand data retrieval module to fetch pitcher statistics for starting pitchers using pybaseball~~

10. ~~Write integration tests for pitcher statistics retrieval with mocked pybaseball calls~~

11. ~~Write integration tests for pitcher statistics retrieval and using actual calls to pybaseball~~

12. ~~Create data structures for team statistics (Bat, HR%, BsR, Bull, Def, Pay, Age, Luck) with validation, using the formula in vision-and-reqs.md~~

13. ~~Write unit tests for team statistics data structures with hardcoded test data~~

14. ~~Expand data retrieval module to fetch team statistics using pybaseball~~

15. ~~Write integration tests for team statistics retrieval with mocked pybaseball calls~~

16. ~~Write integration tests for team statistics retrieval with actual calls to pybaseball~~

17. ~~Implement pNERD calculator with z-score calculations, caps, and positive-only rules~~

18. ~~Write comprehensive unit tests for pNERD calculator with known inputs and expected outputs~~

19. ~~Implement tNERD calculator with z-score calculations, caps, and positive-only rules~~

20. ~~Write comprehensive unit tests for tNERD calculator with known inputs and expected outputs~~

21. ~~Create game score calculator that orchestrates pNERD and tNERD calculations to produce gNERD scores~~

22. ~~Write unit tests for game score calculator with hardcoded pitcher and team data~~

23. ~~Update CLI app to in addition show game score for each game, and order the displayed games not by game time but by game score in descending order~~

24. ~~Create new CLI app that outputs a markdown file with a row per game, following the instructions here:~~

- ~~The contents of the file match the structure and data described later in this TODO item.~~
- ~~It's ok to use the rough code that's already in the cli.py file as a model for how to retrieve data and generate the outputs described here, but the code here should be cleaner. For example, you should factor out functionality so that it lives with the data it uses rather than put the functionality in this new script - so, for example, code that's concerned with formatting a link for a pitcher should be moved to something like pitcher_stats.py, and then called from this script. There should be unit tests for this modularized functionality too, like always.~~
- ~~The CLI app should optionally take a date that specifies the day for which games are shown, in a format like '2025-07-20' and if no date is provided should use today's date.~~
- ~~The filename of the produced markdown file should be in the format mlb_what_to_watch_2025_07_20.md.~~
- ~~The CLI app should be named mlbw-markdown. You can update pyproject.toml with this new name.~~
- ~~The generated markdown file should include a metadata block at the very top with this data, in between --- delimiters:~~
  ~~title: "MLB: What to watch on July 20, 2025"\n~~
  ~~date: 2025-07-20\n~~
  ~~tags: mlbw\n~~
- ~~After the metadata block and before the table generated from the game data, include a short text block that says "Watch these games today:". After the table include text that says "And here's a footer, which someone can modify later.". While you shouldn't need to use a templating engine like Jinja - likely overkill - organize the code so that's it's easy for a user to modify the tags, and the before and after text. For example, you probably want to use a here document.~~
- ~~Output logging statements that describe what you're doing - the date you're using, what data you're retrieving and have retrieved, etc. This script will be run from a GitHub action on a different machine and so the output will be helpful in diagnosing issues when the script doesn't run successfully.~~
- ~~In addition to the unit tests already mentioned above, create a basic one or a few integration tests to verify that the whole CLI app runs and outputs the described markdown file.~~
- ~~Be careful to not duplicate functionality already defined elsewhere in this project. If the functionality needs to be used from multiple scripts or locations, factor it out to a single location (co-locating code that uses particular data) and call it from this tool and from other locations.~~
- ~~For the table, use this header row: | Score | Time (EDT) | Visitors | Score | Home | Score | Starter (V) | Score | Starter (H) | Score |.~~
- ~~And for the table, here's an exemplary data row: | 13.9 | 2:20p | [Boston Red Sox](https://www.fangraphs.com/teams/red-sox/stats) | 6.7 | [Chicago Cubs](https://www.fangraphs.com/teams/cubs/stats) | 9.6 | [Garrett Crochet](https://www.fangraphs.com/search?q=Crochet) | 3.3 | [Cade Horton](https://www.fangraphs.com/search?q=Horton) | 8.2 |.~~

25. Set up GH action that runs the mlbw-markdown script on a schedule, every morning at 8a Pacific time, and generates a markdown file for the given day. I should also be able to run this action manually for testing.

26. Extend the GH action from just above so that when the newly-created markdown file is created successfully the action checks it in to the main branch of the https://github.com/aenfield/blog-eleventy/ repo, copying the file to the directory <repo root>/content/blog/mlbw directory.

## Notes for possible integration and enhancement

- Review and as needed add additional end-to-end integration tests for complete workflow from date input to score output
- Review error handling for missing data, API failures, and edge cases throughout the application, and add/augment where useful
- Check for need for additional tests to improve error handling - for example, missing pitchers, API timeouts, invalid dates
- Add retry logic for pybaseball API calls
- Enhance comprehensive logging throughout the application for debugging and monitoring
- Create comprehensive documentation with usage examples and API reference
- JSON output for use for example as an API/from a server?

## Additional TODO possibilities, depending on need

- In diagnostics output, show the components of the pNERD and tNERD calcs, not just the raw stats and the z-scores - this'd make it easier to see/visually know where the overall scores come from because it'd show where things (like pitcher luck) are divided and where signs are changed (pitcher pace).
- Think about adding logging in a bunch of places perhaps ultimately as part of generating LLM-readable/understandable text that says from top to bottom what the code's doing and where it has problems (when it has problems).
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
