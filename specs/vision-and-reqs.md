# Vision and Requirements

## Project Name

- MLB Watchability.

## Problem Statement

- When you're spoiled for choice with many MLB games every day, which game(s) should you watch? This project calculates a overall "Game NERD score" metric for each game happening on a given day - games with higher scores are more watchable. Carson Cistuli at FanGraphs came up with this approach and frequently published blog posts with a table showing scores for the day along with some analysis/discussion text, but he stopped around 2017 or so.

## Users and Stakeholders

- People that like watching MLB games and have access to MLB.TV (or radio broadcasts) so they can easily watch or listen to any game.

## Statistics/input data and NERD score calculation details

- "Game NERD Score" (or gNERD) is the average of the "Pitcher NERD Score" (pNERD) for each of the two starting pitchers plus the average of the "Team NERD Score" (tNERD) for each of the two teams. Each game has its own gNERD.

### Pitcher NERD - pNERD

The pNERD score comes from these pitcher-specific statistics and exists for each of the starting pitchers in each game:

- xFIP-
- Swinging-Strike Rate (SwStrk)
- Strike Rate (Strk) - it looks like this isn't available directly and already calculated via pybaseball.pitching_stats (which I think comes from Fangraph's pitching stats), so for this one get the total strikes ('Strikes') and divide by total pitches ('Pitches')
- Velocity (Velo) - use the 'FBv' stat (there are other fields that have data from different sources - Statcast and Pitch Info - but FBv exists for more pitchers)
- Age
- Pace (faster/smaller is better)
- ERA- minus xFIP- (Luck) - pitchers that have been unlucky in the sense that their ERA is higher than the corresponding defense-independent stat can be expected regress (positively, which is a good thing to watch), i.e. a pitcher with an ERA- of 110 (10% worse than average) with an xFIP- of 95 (5% better than average) would be expected to have a better ERA- (and ERA) in the future, so if this value is positive it's a good thing
- Knuckleball Rate (KN) - for pitchers that don't throw knucklers, this will be NaN, so be sure that a lack of this number doesn't crash anything - instead, pitchers with a NaN should just get zero contribution for KN rate

The formula for pNERD is (zxFIP- _ 2) + (zSwStrk / 2) + (zStrk / 2) + zVelo + zAge + (zPace / 2) + (Luck / 20) + (KN _ 5) + Constant. Any variable preceded by a z represents the z-score — or standard deviations from the mean — of the relevant metric. The population used for determining the mean in this case includes all pitchers who’ve thrown 20 innings as a starter. Players are never assessed negative, but only positive, scores for Velo, Age, and Luck, so any number that would be below zero is simply rendered as zero. Note that Velo and Age are capped at 2.0; Luck, at 1.0. The constant at the moment is about 3.8.

### Team NERD - tNERD

In contrast to pNERD, the tNERD calculation I'm using is different from the historical/original tNERD - it has the same goal and rough components, but uses mostly different statistics. The original tNERD was developed around 2010, and used a bunch of stats that aren't available today via Fangraphs (accessed via pybaseball). Fortunately, I think there are good replacements for the original stats, and so I've put together a first cut as below. (I'm not an expert, and could easily be wrong - there might be better stats, for example - but this is a start.)

The tNERD score comes from these team-specific statistics:

- Park-adjusted batting runs above average based on wOBA ('Bat' field) - use pybaseball
- Barrel % ('Barrel%') - use pybaseball, note that barrel % is generally park-independent (barrel rate doesn't change much in Colorado, but the outcome from barrels does)
- Base running runs above average ('BsR') - use pybaseball
- Fielding runs above average ('Fld') - use pybaseball
- Payroll, where below average is better ('Pay') - retrieve this data from the static file at data/payroll-spotrac.2025.csv (it's not available from pybaseball)
- Batter age, where younger is better ('Age') - retrieve this data from the static file at data/payroll-spotrac.2025.csv (pybaseball does have age, but it seems a bit less precise, FWIW)
- Luck - calculate as 'wRC' minus 'Runs', use pybaseball; this is expected runs minus actual runs, so teams that have been unlucky by scoring fewer runs than expected get a positive luck boost, as they can be expected to regress (positively); note that the order around the substraction is opposite than for pNERD luck because the stats used for pNERD luck are better when lower while the stats used here for tNERD luck are better when higher

The formula for tNERD is zBat + zBarrel% + zBsR + zFld + zPay + zAge + zLuck + Constant. As with pitcher NERD, any variable preceded by a z represents the z-score of the relevant metric — in this case, relative to averages for the whole league. Teams are never assessed negative, but only positive, scores for Pay, Age, and Luck, so any number that would be below zero is simply rendered as zero. Luck is capped at 2.0. The constant for team NERD is currently at 4.0 (I may change this in the future)

In the future I could extend tNERD to include additional things, like the following, but won't do this to start - the basic idea is to try to capture as metrics different things that make a team fun to watch/listen to:

- Something about bullpen - right now the non-age and payroll parts of tNERD leave out the pitchers, which is logical because we have pNERD for the starter, but that does mean we don't have anything for the bullpen, and lockdown bullpens are fun to watch; the old one had bullpen xFIP, but I don't see any team-specific and bullpen-only/non-starter stats so I'd have to do more
- Goodness of the park
- Goodness of the broadcast teams
- There might be more ideas in some of the references below

### Additional NERD notes

This section has a few historical notes and more data on NERD. Note again that the specific details we're using are described in the document above - the stuff in the resources at the links below is for background, and is overridden by the specifics above. For example, again as noted already, the tNERD we specify above is substantially different from the historical tNERD described in the references below.

- For more details of the score calculations, see https://blogs.fangraphs.com/nerd-scores-return-with-something-not-unlike-a-vengeance/ and https://blogs.fangraphs.com/one-night-only-previews-for-weekend-of-may-13th/.
- For background on why team NERD is what it is, which is interesting by itself and also useful because on its face it doesn't look like at least a decent number of the stats he chose originally (15 years ago) aren't (or are no longer because they've been superceded?) available from the Fangraphs team stats pages, so it probably makes sense to update them, and I can work from his thought process, Carson on [team NERD](https://blogs.fangraphs.com/introducing-team-nerd).

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
