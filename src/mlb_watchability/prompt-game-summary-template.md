## Context

You are analyzing an MLB game for "watchability", using as input "game NERD scores" (gNERD) and supporting statistics. The project helps baseball fans identify the most entertaining games to watch each day. The gNERD score combines pitcher-specific statistics (pNERD) and team-specific statistics (tNERD) to generate an overall watchability score for each game.

## Game Details

**Date:** {{ game_date }}
**Teams:** {{ away_team }} @ {{ home_team }}
**Game Time:** {{ game_time }}
**Starting Pitchers:** {{ away_starter }} vs {{ home_starter }}

## NERD Scores

- **Game NERD (gNERD):** {{ "%.2f"|format(gnerd_score) }}
- **Average Team NERD:** {{ "%.2f"|format(average_team_nerd) }}
  - {{ away_team }} tNERD: {{ "%.2f"|format(away_team_nerd) }}
  - {{ home_team }} tNERD: {{ "%.2f"|format(home_team_nerd) }}
- **Average Pitcher NERD:** {{ "%.2f"|format(average_pitcher_nerd) }}
  - {{ away_starter }} pNERD: {{ "%.2f"|format(away_pitcher_nerd) }}
  - {{ home_starter }} pNERD: {{ "%.2f"|format(home_pitcher_nerd) }}

## Historic and today's games context

Historically, gNERD scores range approxiately between 3 and 18. tNERD between 0 and 10, and pNERD between -2 and 15. There are occasionally scores higher or lower than these ranges.

{% if min_gnerd is defined -%}

- **Game NERD scores today** range from {{ "%.2f"|format(min_gnerd) }} to {{ "%.2f"|format(max_gnerd) }} (average: {{ "%.2f"|format(avg_gnerd) }})
- **Team NERD scores today** range from {{ "%.2f"|format(min_team_nerd) }} to {{ "%.2f"|format(max_team_nerd) }} (average: {{ "%.2f"|format(avg_team_nerd) }})
- **Pitcher NERD scores today** range from {{ "%.2f"|format(min_pitcher_nerd) }} to {{ "%.2f"|format(max_pitcher_nerd) }} (average: {{ "%.2f"|format(avg_pitcher_nerd) }})
  {% endif %}

## Supporting Statistics

Most lines have a calculated number, the z-score of that calculated number, and then, after the "->" a bolded final component. The component is the most important, as it's what goes into the actual NERD score. If the bolded component is positive, that's good and if it's negative that's bad.

### {{ away_team }} Team Stats (tNERD: {{ "%.2f"|format(away_team_nerd) }})

- Batting Runs: {{ "%.1f"|format(away_batting_runs) }} (z-score: {{ "%.2f"|format(away_z_batting_runs) }}) -> **{{ "%.2f"|format(away_batting_component) }}**
- Barrel Rate: {{ "%.3f"|format(away_barrel_rate) }} (z-score: {{ "%.2f"|format(away_z_barrel_rate) }}) -> **{{ "%.2f"|format(away_barrel_component) }}**
- Baserunning Runs: {{ "%.1f"|format(away_baserunning_runs) }} (z-score: {{ "%.2f"|format(away_z_baserunning_runs) }}) -> **{{ "%.2f"|format(away_baserunning_component) }}**
- Fielding Runs: {{ "%.1f"|format(away_fielding_runs) }} (z-score: {{ "%.2f"|format(away_z_fielding_runs) }}) -> **{{ "%.2f"|format(away_fielding_component) }}**
- Payroll: ${{ "%.1f"|format(away_payroll) }}M (z-score: {{ "%.2f"|format(away_z_payroll) }}) -> **{{ "%.2f"|format(away_payroll_component) }}**
- Age: {{ "%.1f"|format(away_age) }} (z-score: {{ "%.2f"|format(away_z_age) }}) -> **{{ "%.2f"|format(away_age_component) }}**
- Luck: {{ "%.1f"|format(away_luck) }} (z-score: {{ "%.2f"|format(away_z_luck) }}) -> **{{ "%.2f"|format(away_luck_component) }}**

### {{ home_team }} Team Stats (tNERD: {{ "%.2f"|format(home_team_nerd) }})

- Batting Runs: {{ "%.1f"|format(home_batting_runs) }} (z-score: {{ "%.2f"|format(home_z_batting_runs) }}) -> **{{ "%.2f"|format(home_batting_component) }}**
- Barrel Rate: {{ "%.3f"|format(home_barrel_rate) }} (z-score: {{ "%.2f"|format(home_z_barrel_rate) }}) -> **{{ "%.2f"|format(home_barrel_component) }}**
- Baserunning Runs: {{ "%.1f"|format(home_baserunning_runs) }} (z-score: {{ "%.2f"|format(home_z_baserunning_runs) }}) -> **{{ "%.2f"|format(home_baserunning_component) }}**
- Fielding Runs: {{ "%.1f"|format(home_fielding_runs) }} (z-score: {{ "%.2f"|format(home_z_fielding_runs) }}) -> **{{ "%.2f"|format(home_fielding_component) }}**
- Payroll: ${{ "%.1f"|format(home_payroll) }}M (z-score: {{ "%.2f"|format(home_z_payroll) }}) -> **{{ "%.2f"|format(home_payroll_component) }}**
- Age: {{ "%.1f"|format(home_age) }} (z-score: {{ "%.2f"|format(home_z_age) }}) -> **{{ "%.2f"|format(home_age_component) }}**
- Luck: {{ "%.1f"|format(home_luck) }} (z-score: {{ "%.2f"|format(home_z_luck) }}) -> **{{ "%.2f"|format(home_luck_component) }}**

### {{ away_starter }} Pitcher Stats (pNERD: {{ "%.2f"|format(away_pitcher_nerd) }})

{% if away_pitcher_has_stats %}

- xFIP-: {{ "%.1f"|format(away_pitcher_xfip_minus) }} (z-score: {{ "%.2f"|format(away_pitcher_z_xfip_minus) }}) -> **{{ "%.2f"|format(away_pitcher_xfip_component) }}**
- SwStr%: {{ "%.1f"|format(away_pitcher_swinging_strike_rate) }}% (z-score: {{ "%.2f"|format(away_pitcher_z_swinging_strike_rate) }}) -> **{{ "%.2f"|format(away_pitcher_swinging_strike_component) }}**
- Strike%: {{ "%.1f"|format(away_pitcher_strike_rate) }}% (z-score: {{ "%.2f"|format(away_pitcher_z_strike_rate) }}) -> **{{ "%.2f"|format(away_pitcher_strike_component) }}**
- Velocity: {{ "%.1f"|format(away_pitcher_velocity) }} mph (z-score: {{ "%.2f"|format(away_pitcher_z_velocity) }}) -> **{{ "%.2f"|format(away_pitcher_velocity_component) }}**
- Age: {{ away_pitcher_age }} (z-score: {{ "%.2f"|format(away_pitcher_z_age) }}) -> **{{ "%.2f"|format(away_pitcher_age_component) }}**
- Pace: {{ "%.1f"|format(away_pitcher_pace) }}s (z-score: {{ "%.2f"|format(away_pitcher_z_pace) }}) -> **{{ "%.2f"|format(away_pitcher_pace_component) }}**
- Luck: {{ "%.1f"|format(away_pitcher_luck) }} -> **{{ "%.2f"|format(away_pitcher_luck_component) }}**
- KN%: {{ "%.1f"|format(away_pitcher_knuckleball_rate) }}% -> **{{ "%.2f"|format(away_pitcher_knuckleball_component) }}**
  {% else %}
  No detailed stats available
  {% endif %}

### {{ home_starter }} Pitcher Stats (pNERD: {{ "%.2f"|format(home_pitcher_nerd) }})

{% if home_pitcher_has_stats %}

- xFIP-: {{ "%.1f"|format(home_pitcher_xfip_minus) }} (z-score: {{ "%.2f"|format(home_pitcher_z_xfip_minus) }}) -> **{{ "%.2f"|format(home_pitcher_xfip_component) }}**
- SwStr%: {{ "%.1f"|format(home_pitcher_swinging_strike_rate) }}% (z-score: {{ "%.2f"|format(home_pitcher_z_swinging_strike_rate) }}) -> **{{ "%.2f"|format(home_pitcher_swinging_strike_component) }}**
- Strike%: {{ "%.1f"|format(home_pitcher_strike_rate) }}% (z-score: {{ "%.2f"|format(home_pitcher_z_strike_rate) }}) -> **{{ "%.2f"|format(home_pitcher_strike_component) }}**
- Velocity: {{ "%.1f"|format(home_pitcher_velocity) }} mph (z-score: {{ "%.2f"|format(home_pitcher_z_velocity) }}) -> **{{ "%.2f"|format(home_pitcher_velocity_component) }}**
- Age: {{ home_pitcher_age }} (z-score: {{ "%.2f"|format(home_pitcher_z_age) }}) -> **{{ "%.2f"|format(home_pitcher_age_component) }}**
- Pace: {{ "%.1f"|format(home_pitcher_pace) }}s (z-score: {{ "%.2f"|format(home_pitcher_z_pace) }}) -> **{{ "%.2f"|format(home_pitcher_pace_component) }}**
- Luck: {{ "%.1f"|format(home_pitcher_luck) }} -> **{{ "%.2f"|format(home_pitcher_luck_component) }}**
- KN%: {{ "%.1f"|format(home_pitcher_knuckleball_rate) }}% -> **{{ "%.2f"|format(home_pitcher_knuckleball_component) }}**
  {% else %}
  No detailed stats available
  {% endif %}

## Instructions

- Before writing your summary, search the web for the latest news, injury reports, recent performance, and storylines related to this specific game, both teams, and starting pitchers. Query for the game with the date and time specified above, to avoid getting information about other games that have similar teams and/or pitchers.
- Start your summary with one or two bold sentences that capture the essence of why this game is worth watching (or not). This should summarize your overall assessment before diving into details. The summary should be more than just stating the gNERD number and how it relates to other games/history. If necessary, generate a draft summary so you know what you'll say, and then go back and add the summary at the top.
- Overall, explain why this game is more or less watchable based on NERD components, supplemented by what you learned in your web searches.
- Don't use bullets or emojis or different sections: just keep it to sentences.
- Write in a witty and wry but still engaging tone that helps viewers understand why they should (or shouldn't) prioritize this game. Avoid hyperbolic language - not every game is 'exceptional', 'fascinating', 'remarkable', 'jaw-dropping', 'intriguing', or 'classic'. Instead, leave out unnecessary adjectives unless something is truly noteworthy.
- Highlight pitcher performances for pitchers with high pNERD scores and particular points of novelty (like rookies making debuts, long-time pitchers returning from injuries), etc. Note that pNERD scores of 0 indicate we don't have statistical data available for that pitcher.
- **Only** if there are particularly interesting things, consider including one or at most a few of the following possibilties, while erring on the side of leaving something out unless it's interesting:
  - Notable team metrics that contribute to entertainment value
  - Interesting matchups or statistical contrasts
  - Interesting current storylines that add to watchability
  - Items of interesting historical significance, rivalries, etc.
- Prefer more analytically-minded statistics while also not short-changing useful standard statistics. For example, IP, strikeouts, walks, HRs, xFIP, FIP, and WAR are all good, while RBI and ERA generally aren't. Use xFIP or FIP instead of ERA when discussing pitching effectiveness.
- Use the "Historic and today's games context" section to understand where this game's NERD scores rank relative to other games historically and to today. This context should inform your assessment of watchability - a game with scores near the maximum ranges is more compelling than one near the minimums. (Further, this implementation of NERD scores doesn't have scores that always range from 0-10; it doesn't follow the original Cistulli scores.)
- "Momentum" is not a thing, despite what you might read on the web. Just because a team or pitcher has had recent performance that's out of line with their underlying skill-based statistics doesn't mean they're likely to continue over/under performing. Ignore articles that say that this is the case.
- Don't worry about mentioning the "Luck" component when it's relatively small... wait until the final component number gets to above 0.75 or so, at a minimum. The luck component is positive when a team or pitcher is underperforming their skill-based statistics, and so is likely to regress positively to better performance.
- Don't discuss the time or date of the game - don't say 'this afternoon's game', etc. You don't know when someone will read the summary.
- If there's not much to say for a particular instruction, leave it out - prefer being concise and only saying things when they're worthwhile.

Now, following the above instructions, create a **concise** summary. Don't preface or follow your summary with text that's not part of the summary. The summary should have approximately 150-175 words. After you've finished the summary, check to make sure it's not too long, and shorten it - still following the instructions above - if needed.
