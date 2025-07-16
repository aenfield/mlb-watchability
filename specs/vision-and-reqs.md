# Vision and Requirements

## Project Name

- MLB Watchability.

## Problem Statement

- When you're spoiled for choice with many MLB games every day, which game(s) should you watch? This project calculates a overall "Game NERD score" metric for each game happening on a given day - games with higher scores are more watchable. Carson Cistuli at FanGraphs came up with this approach and frequently published blog posts with a table showing scores for the day along with some analysis/discussion text, but he stopped around 2017 or so.

## Users and Stakeholders

- People that like watching MLB games and have access to MLB.TV (or radio broadcasts) so they can easily watch or listen to any game.

## Statistics/input data and NERD score calculation details

- "Game NERD Score" (or gNERD) is the average of the "Pitcher NERD Score" (pNERD) for each of the two starting pitchers plus the average of the "Team NERD Score" (tNERD) for each of the two teams. Each game has its own gNERD.
- The pNERD score comes from these pitcher-specific statistics and exists for each of the starting pitchers in each game:
  - xFIP-
  - Swinging-Strike Rate (SwStrk)
  - Strike Rate (Strk) - it looks like this isn't available directly and already calculated via pybaseball.pitching_stats (which I think comes from Fangraph's pitching stats), so for this one get the total strikes ('Strikes') and divide by total pitches ('Pitches')
  - Velocity (Velo) - use the 'FBv' stat (there are other fields that have data from different sources - Statcast and Pitch Info - but FBv exists for more pitchers)
  - Age
  - Pace
  - ERA- minus xFIP- (Luck)
  - Knuckleball Rate (KN) - For pitchers that don't throw knucklers, this will be NaN, so be sure that a lack of this number doesn't crash anything - instead, pitchers with a NaN should just get zero contribution for KN rate
- The formula for pNERD is (zxFIP- _ 2) + (zSwStrk / 2) + (zStrk / 2) + zVelo + zAge + (zPace / 2) + (Luck / 20) + (KN _ 5) + Constant. Any variable preceded by a z represents the z-score — or standard deviations from the mean — of the relevant metric. The population used for determining the mean in this case includes all pitchers who’ve thrown 20 innings as a starter. Players are never assessed negative, but only positive, scores for Velo, Age, and Luck, so any number that would be below zero is simply rendered as zero. Note that Velo and Age are capped at 2.0; Luck, at 1.0. The constant at the moment is about 3.8.
- The tNERD score comes from these team-specific statistics:
  - Park-Adjusted Batting Runs Above Average (Bat)
  - Park-Adjusted Home Run Rate (HR%)
  - Baserunning Runs (BsR)
  - Bullpen xFIP (Bull)
  - Defensive Runs (Def)
  - Payroll, Where Below Average Is Better (Pay)
  - Batter Age, Where Younger Is Better (Age)
  - Expected Wins, Per WAR, Minus Actual Wins (Luck)
- The formula for tNERD is zBat + zHR% + zBsR + (zBull / 2) + (zDef / 2) + zPay + zAge + (Luck / 2) + Constant. As with pitcher NERD, any variable preceded by a z represents the z-score of the relevant metric — in this case, relative to averages for the whole league. Teams are never assessed negative, but only positive, scores for Pay, Age, and Luck, so any number that would be below zero is simply rendered as zero. Note that Luck is capped at 2.0. The constant for team NERD is currently at about 4.0.
- For more details of the score calculations, see https://blogs.fangraphs.com/nerd-scores-return-with-something-not-unlike-a-vengeance/ and https://blogs.fangraphs.com/one-night-only-previews-for-weekend-of-may-13th/.

## Requirements

- One module should calculate the pNERD and tNERD scores for each game on a given day and then use these scores to generate a tNERD score for each game. The module should return a JSON array with a row for each game, where each row has the two teams, the pNERD, tNERD, and gNERD scores, the names of the starting pitchers, and the time of the game.
- Another module should obtain the data required to calculate the NERD scores. Ideally only the data needed for the calculation of the scores should be retrieved - i.e., only data for starting pitchers for the specified day should be retrieved, not data for all pitchers. For the statistics needed for team NERD, the module should heavily prefer data that's already calculated - for example, for "Baserunning Runs" it should look for and use source data that already has this number calculated for each team. It should not try to retrieve and then calculate a team-specific number using all of the raw underlying data - like rows for each player - unless that's the only way to calculate the team-specific number.
- A console application that obtains the data and calculates the NERD scores, using the previously introduced modules, and then prints the team, game time, and scores to stdout. (Eventually I'll make this data available online in some fashion, but will start with this simple command line application.)
- Each of the calculation and data retrieval modules should have tests. For example, the calculation module should use static and hardcoded input data (statistics) and verify that the calculations give the correct results. For the data retrieval module, I suppose at least some of the tests are more integration-like, and validate that data can actually be retrieved from the Internet. These don't need to and can't test the actual retrieved data is correct (since we don't have known ground truth, unless we want to use historical data or some other second source, and we don't need to do that for now). I should be able to run the tests from the command line and from a GitHub Actions CI/CD workflow.

## Constraints

- Use a recent version of Python.
- For retrieving the data, both the list of games on a given day (teams, game time, names of starting pitchers) and the pitcher and team statistics required to calculate the NERD scores, try to use the pybaseball library at https://github.com/jldbc/pybaseball.
- Manage the Python version and Python libraries using UV, not pip. For example, the project should have a top-level pyproject.toml file that specifies the Python version and dependencies, and I should be able to run the aforementioned command line application with a UV command like 'uv run mlb-watchability-cmd'.

## Risks and Unknowns

- I don't yet know what's unclear or what assumptions I'm making. :-)
