# MLB Game Watchability Summary Request

## Project Context

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

- xFIP-: {away_xfip_minus:.0f} (z-score: {away_z_xfip_minus:.2f})
- Swinging Strike Rate: {away_swinging_strike_rate:.3f} (z-score:
  {away_z_swinging_strike_rate:.2f})
- Strike Rate: {away_strike_rate:.3f} (z-score: {away_z_strike_rate:.2f})
- Velocity: {away_velocity:.1f} mph (z-score: {away_z_velocity:.2f})
- Age: {away_pitcher_age} (z-score: {away_z_pitcher_age:.2f})
- Pace: {away_pace:.1f}s (z-score: {away_z_pace:.2f})
- Luck (ERA- minus xFIP-): {away_luck_pitcher:.1f}
- Knuckleball Rate: {away_knuckleball_rate:.3f}

### {home_starter} Pitcher Stats (pNERD: {home_pitcher_nerd:.2f})

- xFIP-: {home_xfip_minus:.0f} (z-score: {home_z_xfip_minus:.2f})
- Swinging Strike Rate: {home_swinging_strike_rate:.3f} (z-score:
  {home_z_swinging_strike_rate:.2f})
- Strike Rate: {home_strike_rate:.3f} (z-score: {home_z_strike_rate:.2f})
- Velocity: {home_velocity:.1f} mph (z-score: {home_z_velocity:.2f})
- Age: {home_pitcher_age} (z-score: {home_z_pitcher_age:.2f})
- Pace: {home_pace:.1f}s (z-score: {home_z_pace:.2f})
- Luck (ERA- minus xFIP-): {home_luck_pitcher:.1f}
- Knuckleball Rate: {home_knuckleball_rate:.3f}

## Instructions

1. **Search for Current Information:** Before writing your summary, search the web for the latest
   news, injury reports, recent performance, and storylines related to this specific game, both teams,
   and starting pitchers.

2. **Write a Concise Summary:** Based on the NERD scores and your web research, create a **single
   paragraph** summary that follows the following detailed instructions. Don't use bullets or emojis or
   different sections: just keep it to sentences.

   - Explain why this game is or isn't watchable based on the specific NERD components
   - Highlight standout pitcher performances (for pitchers with high pNERD scores)
   - Mention exceptional team metrics that contribute to entertainment value
   - Highlight any interesting matchups or statistical contrasts
   - Include any current storylines that add to the watchability
   - Mention any historical significance, rivalries, or player narratives
   - Prefer more analytically-minded statistics while also not short-changing useful standard statistics. For example, IP, strikeouts, HRs, xFIP and xFIP, WAR are all good, while RBI, ERA, etc. aren't.

3. **Keep it Conversational:** Write in an engaging, fan-friendly tone that helps viewers
   understand why they should (or shouldn't) prioritize this game among their viewing options. Be wry and witty.

4. **Be Specific:** Reference the actual NERD scores and key statistics that drive your
   recommendations.
