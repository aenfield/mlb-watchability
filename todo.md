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

25. ~~Set up GH action that runs the mlbw-markdown script on a schedule, every morning at 8a Pacific time, and generates a markdown file for the given day. I should also be able to run this action manually for testing.~~

26. ~~Extend the GH action from just above so that when the newly-created markdown file is created successfully the action checks it in to the main branch of the https://github.com/aenfield/blog-eleventy/ repo, copying the file to the directory <repo root>/content/blog/mlbw directory.~~

## Expand to generate and show details

27. ~~As part of https://github.com/aenfield/mlb-watchability/issues/6, I first want to expand the pitcher_stats.py and team_stats.py implementations to expose the components of the pNERD/tNERD score. We can probably do this by factoring the relevant code from the pitcher_nerd_breakdown.py and team_nerd_breakdown.py first cut implementations into the pitcher/team stats implementations - in the end, PitcherNerdStats/TeamNerdStats should have properties with the components, and the components should sum to pNERD/tNERD score. Then make pitcher_nerd_breakdown.py and team_nerd_breakdown.py use the new PitcherNerdStats/TeamNerdStats implementations, make sure existing tests pass, and add new tests for the new location of the functionality.~~

28. ~~Now, continuing with implementing https://github.com/aenfield/mlb-watchability/issues/6, I want to do a first cut at the expanded UI. For this one, I want to add a new set of tables to the Markdown file created by mlbw-markdown, after the existing table. The format should look like this, with one section like this for each game.~~

# Detail

## Milwaukee Brewers @ Seattle Mariners, 9:40p

### Milwaukee Brewers

|              | Batting Runs | Barrel % | Baserunning | Fielding | Payroll | Age   | Luck | Constant | TOTAL |
| ------------ | ------------ | -------- | ----------- | -------- | ------- | ----- | ---- | -------- | ----- |
| **Raw Stat** | 59.8         | 10.0%    | -4.2        | -14.7    | $152.8M | 28.2  | 16.0 | —        | —     |
| **Z-Score**  | 1.23         | 0.46     | -0.87       | -0.86    | -0.27   | -0.53 | 0.90 | —        | —     |
| **tNERD**    | 1.23         | 0.46     | -0.87       | -0.86    | 0.27    | 0.53  | 0.90 | 4.00     | 5.67  |

### Seattle Mariners

|              | Batting Runs | Barrel % | Baserunning | Fielding | Payroll | Age   | Luck | Constant | TOTAL |
| ------------ | ------------ | -------- | ----------- | -------- | ------- | ----- | ---- | -------- | ----- |
| **Raw Stat** | 59.8         | 10.0%    | -4.2        | -14.7    | $152.8M | 28.2  | 16.0 | —        | —     |
| **Z-Score**  | 1.23         | 0.46     | -0.87       | -0.86    | -0.27   | -0.53 | 0.90 | —        | —     |
| **tNERD**    | 1.23         | 0.46     | -0.87       | -0.86    | 0.27    | 0.53  | 0.90 | 4.00     | 5.67  |

### Visiting starter: Jacob Misiorowski

|              | xFIP- | SwStr% | Strike % | Velocity | Age   | Pace  | Luck | KN%  | Constant | TOTAL |
| ------------ | ----- | ------ | -------- | -------- | ----- | ----- | ---- | ---- | -------- | ----- |
| **Raw Stat** | 76.0  | 13.8%  | 64.7%    | 98.1 mph | 23    | 18.6s | -31  | 0.0% | —        | —     |
| **Z-Score**  | -1.51 | 1.66   | 0.30     | 2.02     | -1.49 | 0.07  | —    | —    | —        | —     |
| **pNERD**    | 3.01  | 0.83   | 0.15     | 2.00     | 1.49  | -0.04 | 0.00 | 0.00 | 3.80     | 11.25 |

### Home starter: Logan Gilbert

|              | xFIP- | SwStr% | Strike % | Velocity | Age   | Pace  | Luck | KN%  | Constant | TOTAL |
| ------------ | ----- | ------ | -------- | -------- | ----- | ----- | ---- | ---- | -------- | ----- |
| **Raw Stat** | 76.0  | 13.8%  | 64.7%    | 98.1 mph | 23    | 18.6s | -31  | 0.0% | —        | —     |
| **Z-Score**  | -1.51 | 1.66   | 0.30     | 2.02     | -1.49 | 0.07  | —    | —    | —        | —     |
| **pNERD**    | 3.01  | 0.83   | 0.15     | 2.00     | 1.49  | -0.04 | 0.00 | 0.00 | 3.80     | 11.25 |

~~The example section ends here. There should be a section like the above for each game.~~

29. ~~Add within-page links in the table at the top that go to specific detail section for the game below, using anchors and fragments - i.e., with # in the link. If the user clicks on the overall game score it sholud go to the top of the section and if they click on one of the tNERD or pNERD scores it should go to that specific part of the section.~~

## Use an LLM to generate game descriptions

(I've worked on this a little bit before adding TODOs, for exploration and to create the start of an LLM abstraction layer in llm_client, so not everything I've done here is a checked of TODO here.)

30. ~~Expand the generate_text_from_llm function in llm_client.py to take a boolean parameter called 'include_web_search' that defaults to false. If false, do things like you do now. If true, though, tell the LLM it's ok to do a web search. Change the abstract base class stuff only if required. For the specific Anthropic implementation changes, refer to claude_api.py to see how things work - specifically, the changes in the client.messages.create call to include "name": "web_search" and "max_uses": max_web_searches (the latter should be set to 1). Also update the return value of generate_text_from_llm to be a tuple where the first element is the text response (like the function already returns), and the second element is a list of 'web_sources' citations. If there are no citations/sources, return an empty list. You don't need to include the additional other stuff in claude_api.py, like figuring out tokens and costs. Add tests for the syntax and calls, but don't yet add any tests that actually call the API and incur charges.~~

31. ~~Add minimal integration tests for #30 that actually call the Anthropic API. Check with and without web search. Use a super simple prompt like 'Generate a short 100 character summary of today's Seattle Mariners game'. For the model, use 'claude-3-5-haiku-latest'. Don't test that any particular text is in the text results since that's brittle.~~

32. ~~Add an instance method to GameScore called 'generate_description' that uses the properties of the GameScore instance - use both game properties and also the detailed team and pitcher properties in the referenced TeamNerdStats and PitcherNerdStats objects - to a) populate a prompt template stored in the src/mlb_watchability/prompt-game-summary-template.md file to generate the description, and b) call a LLM using src/mlb_watchability/llm_client.py - specifically generate_text_from_llm - to retrieve the response. For your tests, use MODEL_STRING_CHEAP to specify the model to use.~~

(I did a bunch more refactoring and tidying up as part of implementing the generate_description method, and also added an mlbw-prompt CLI app to generate a completed prompt and optionally send it to Anthropic.)

33. ~~Expand the functionality used by mlbw-markdown to optionally (controlled by a command line flag "--game_descriptions") include a "Description" section in the detail output, per game, located after the overall header and before the team detail data. For this TODO, we'll work on the change in the markdown with a canned description that you can generate creatively to show "A concise summary of the next Mariners game, consisting of about 150-175 words".~~

34. ~~The GameScore should manage descriptions, so, first, add new game_description and game_description_sources properties to the GameScore class. Each of these is None to start. Modify from_games to set these properties depending on two new optional parameters to from_games. The first new parameter, "game_desc_source", defaults to None and can also be either "canned", in which case the game_description is set to the canned description just below, or "llm", in which case the game_description property is set to the first part of the tuple response from calling GameScore::generate_description and the game_description_sources property is set to the second part of the tuple from the same call. The second new parameter to from_games is "game_desc_limit", and takes an integer. Only the first game_desc_limit games in the set of GameScore instances created by from_games should have their game_description field set according to game_desc_source. For example, if game_desc_limit is 3, then the first three GameScore instances created by from_games - the ones with the highest game NERD scores - will have their game_description set, and the remaining will keep their default game_description of None. If no game_desc_limit value is provided, assume a value of 1, so only the first game (with the highest game NERD score) will get have their description set. Since which games get descriptions depends on a list of GameScore instances sorted by game NERD score, you probably want to add the code to set the game_description and game_description_sources properties after the line that sorts at the bottom of from_games.~~

~~Canned description text: "A concise summary of this compelling matchup, featuring two teams with distinct strengths and strategic approaches. The visiting team brings their road experience and adaptability, while the home team looks to leverage familiar surroundings and fan support. Both squads showcase interesting statistical profiles across pitching, hitting, and defensive metrics. Key storylines include starting pitcher matchups, offensive production potential, and bullpen depth. Recent team performance suggests this could be a competitive contest with multiple momentum shifts. Strategic decisions from both managers will likely play crucial roles in determining the outcome. Individual player performances could significantly impact team standings and future positioning. This game represents quality baseball with engaging narratives for viewers."~~

35. ~~Update mlbw-markdown to remove --game_descriptions and replace with --game_desc_source which maps to the from_games parameter game_desc_source and so can be either "canned" or "llm", and --game_desc_limit which maps to from_games game_desc_limit and so is an integer. If --game_desc_source is provided but --game_desc_limit is not, then --game_desc_limit is assumed to be 1. If --game_desc_limit is provided but --game_desc_source is not, then --game_desc_source is assumed to be "canned". Pass these values through to from_games and let it do its thing. If neither of these two new args is provided, then mlbw-markdown should not include description fields in the output.~~

36. ~~Do first cut at adding links from the search to the description UI. I can iterate on the UI if I care to, later.~~

## Iterate on usability and UI, especially of new descriptions

37. (Some of this is done.) Lots of opportunities for improving the description output, most of which are tied to updating the prompt. ~~One area is with additional data, like the min/max range of all three NERD scores, and the averages, so the LLM can do a better job of putting actual game-specific scores in the right context (and consider including in the prompt specifically how to use these numbers, and that they outweigh what the model might know from Cistulli's posts, like that the ranges are 0-10).~~ ~~Another is with updates to the instructions for the generated text: a) avoid hyperbole unless something is **really** amazing - not every game is 'exceptional', 'fascinating', 'remarkable', 'jaw-dropping', 'intriguing', 'classic' - instead, just leave out the adjectives in many cases; b) put the bolded summary at the top of the summary (maybe try telling it to review/think and move it if it's having a hard time generating a good summary at the top before it outputs the majority of the text); c) avoid ERA specifically and instead use xFIP or FIP (both of which are on the same as ERA); d) consider adding text to the prompt to explain stats that are custom and for which the model won't have previous knowledge, like Luck, etc.; e) update the stats text in the prompt to say 'Baserunning runs' and 'Fielding runs', and just take a closer look at what's output for these sections and make additional useful tweaks, f) specifically tell it that pNERD scores of 0 mean we don't have data.~~

38. ~~Try shortening up the sources and 'AI-generated' qualifying text to a single line without displayed titles. In Markdown, it would be something like: "[Claude](https://www.anthropic.com/claude) generated this text using instructions, the NERD scores, and these sources: [1], [2], [3]". That is, the current mlbw-markdown implementation outputs a row per source, with a full title - instead I want the title to just be 1, or 2, or 3, etc. and everything to show up on one line.~~

39. ~~Write a quickie data analysis script, in the analysis directory, to understand the basics of the distributions of the calculated pNERD, tNERD, and gNERD scores based on as much historical data as possible. The data comes from the generated .md files in the directory ../blog-eleventy/content/blog/mlbw/. First generate an internal-to-program table with a row per day, and the following columns: date, gNERD score, visiting tNERD, home tNERD, visiting pitcher pNERD, home team pitcher pNERD, visiting team (three letter abbrev), home team (three letter abbrev), visiting pitcher name, home team pitcher name. Parse each each input .md file to get the information for a single row. Save the table to a .csv file in the analysis directory. And finish by printing out summary statistics for gNERD scores, team tNERD scores, and pitcher pNERD scores, including the number of scores, mean, min, max, and percentiles at 0.05, 0.25, 0.5, 0.75, and 0.95.~~

40. ~~Evaluate using the cheaper Haiku model in production instead of Sonnet. I did this already by comparing costs - it's 1/3 the cost to use Haiku (overall, with the token costs going way down and the web search cost staying the same), which means the monthly cost will be ~$15 or less instead of around ~$40, adding an llm-model param to mlbw-markdown to enable choosing the normal or cheap model, and then by doing single-sample eyeball comparison between three games. Overall I may actually like the Haiku summaries better - they're shorter, but still have very similar info (better - Sonnet is too long even though I've asked for shorter); they seem to be less focused on NERD while still including it (Sonnet goes too hard w/ NERD scores and percentiles, etc. even though I've prompted it to not do so), and, hey, it's non-trivially cheaper, especially for someone w/o a job. I'll switch it in production and see how it does over a full slate of games for at least a few days.~~

41. ~~GPT-5 looks pretty good, and it's cheaper than Sonnet 4, and the updated web search pricing matches Anthropic instead of being 2.5x more expensive (for the search, not the tokens). I want to implement a new LLMClient subclass that uses OpenAI, and plumb through the choice of this provider from mlbw-markdown.~~

42. Consider limiting allowed sites for sources via the Anthropic API to a few to prefer content from places like FanGraphs and hopefully other analytical sites with recent info (would also want to make sure there's enough general and recent game-specific info).

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
