## Context

You are analyzing an MLB game for "watchability", using as input "game NERD scores" (gNERD) and
supporting statistics. The project helps baseball fans identify the most entertaining games to watch each day.
The gNERD score combines pitcher-specific statistics (pNERD) and team-specific statistics (tNERD) to generate an
overall watchability score for each game.

## Game Details

**Teams:** {away_team} @ {home_team}
**Game Time:** {game_time}
**Starting Pitchers:** {away_starter} vs {home_starter}

## NERD Scores

- **Game NERD (gNERD):** {gnerd_score:.2f}
- **Average Team NERD:** {average_team_nerd:.2f}
  - {away_team} tNERD: {away_team_nerd:.2f}
  - {home_team} tNERD: {home_team_nerd:.2f}
- **Average Pitcher NERD:** {average_pitcher_nerd:.2f}
  - {away_starter} pNERD: {away_pitcher_nerd:.2f}
  - {home_starter} pNERD: {home_pitcher_nerd:.2f}

## Supporting Statistics

### {away_team} Team Stats (tNERD: {away_team_nerd:.2f})

- Batting Runs: {away_batting_runs:.1f} (z-score: {away_z_batting_runs:.2f})
- Barrel Rate: {away_barrel_rate:.3f} (z-score: {away_z_barrel_rate:.2f})
- Baserunning Runs: {away_baserunning_runs:.1f} (z-score: {away_z_baserunning_runs:.2f})
- Fielding Runs: {away_fielding_runs:.1f} (z-score: {away_z_fielding_runs:.2f})
- Payroll: ${away_payroll:.1f}M (z-score: {away_z_payroll:.2f})
- Age: {away_age:.1f} (z-score: {away_z_age:.2f})
- Luck: {away_luck:.1f} (z-score: {away_z_luck:.2f})

### {home_team} Team Stats (tNERD: {home_team_nerd:.2f})

- Batting Runs: {home_batting_runs:.1f} (z-score: {home_z_batting_runs:.2f})
- Barrel Rate: {home_barrel_rate:.3f} (z-score: {home_z_barrel_rate:.2f})
- Baserunning Runs: {home_baserunning_runs:.1f} (z-score: {home_z_baserunning_runs:.2f})
- Fielding Runs: {home_fielding_runs:.1f} (z-score: {home_z_fielding_runs:.2f})
- Payroll: ${home_payroll:.1f}M (z-score: {home_z_payroll:.2f})
- Age: {home_age:.1f} (z-score: {home_z_age:.2f})
- Luck: {home_luck:.1f} (z-score: {home_z_luck:.2f})

### {away_starter} Pitcher Stats (pNERD: {away_pitcher_nerd:.2f})

{away_pitcher_stats_section}

### {home_starter} Pitcher Stats (pNERD: {home_pitcher_nerd:.2f})

{home_pitcher_stats_section}

## Instructions

- Before writing your summary, search the web for the latest news, injury reports, recent performance, and storylines related to this specific game, both teams, and starting pitchers.
- Overall, explain why this game is more or less watchable based on the specific NERD components, supplemented by what you learned in your web searches.
- Don't use bullets or emojis or different sections: just keep it to sentences.
- Write in a witty and wry but still engaging tone that helps viewers understand why they should (or shouldn't) prioritize this game.
- Highlight pitcher performances for pitchers with high pNERD scores and particular points of novelty (like rookies making debuts, long-time pitchers returning from injuries), etc.
- **Only** if there are particularly interesting things, consider including one or at most a few of the following possibilties, while erring on the side of leaving something out unless it's interesting:
  - Exceptional team metrics that contribute to entertainment value.
  - Interesting matchups or statistical contrasts.
  - Interesting current storylines that add to watchability.
  - Items of interesting historical significance, rivalries, and the like.
- Prefer more analytically-minded statistics while also not short-changing useful standard statistics. For example, IP, strikeouts, HRs, xFIP and xFIP, WAR are all good, while RBI, ERA, etc. generally aren't.
- Don't discuss the time or date of the game - don't say 'this afternoon's game', etc.
- If there's not much to say for a particular instruction, leave it out - prefer being concise and only saying things when they're worthwhile.
- When you output the overall one or two sentences that summarize everything you're saying, which you usually do at the end of the summary, emphasize them by making them bold.

Now, following the above instructions, create a **concise** summary - no more than 150 words. Don't preface or follow your summary with text that's not part of the summary.
