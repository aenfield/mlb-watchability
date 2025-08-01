#!/usr/bin/env python3
"""
Script to generate a game summary prompt by combining template with actual game data.
Takes a specified game from the schedule and populates the prompt template with real NERD data.
Supports selecting games by index, with the first game (index 0) as the default.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import pytz

# Add the project root to the Python path so we can import from src
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root / "src"))

from mlb_watchability.data_retrieval import get_game_schedule
from mlb_watchability.game_scores import GameScore
from mlb_watchability.team_stats import calculate_detailed_team_nerd_scores
from mlb_watchability.pitcher_stats import (
    calculate_detailed_pitcher_nerd_scores,
    find_pitcher_nerd_stats_fuzzy,
)
from mlb_watchability.team_mappings import get_team_abbreviation


def get_game_data(
    date: str = "2025-07-23", season: int = 2025, game_index: int = 0
) -> Dict[str, Any]:
    """Get complete data for the specified game of the day."""

    # Get today's games
    print(f"Retrieving game schedule for {date}...")
    games = get_game_schedule(date)
    if not games:
        raise ValueError(f"No games found for {date}")
    print(f"Found {len(games)} games scheduled")

    # Calculate all game scores to get the specified one with full data
    print("Calculating game NERD scores (this may take a moment)...")
    game_scores = GameScore.from_games(games, season)
    if not game_scores:
        raise ValueError("No games with calculated scores found")

    if game_index >= len(game_scores):
        raise ValueError(
            f"Game index {game_index} is out of range. Only {len(game_scores)} games available."
        )

    selected_game = game_scores[game_index]
    print(f"Selected game: {selected_game.away_team} @ {selected_game.home_team}")

    # Get detailed team and pitcher NERD data
    print("Retrieving detailed team statistics...")
    team_nerd_details = calculate_detailed_team_nerd_scores(season)
    print("Retrieving detailed pitcher statistics...")
    pitcher_nerd_details = calculate_detailed_pitcher_nerd_scores(season)

    # Get team abbreviations for lookup
    away_team_abbr = get_team_abbreviation(selected_game.away_team)
    home_team_abbr = get_team_abbreviation(selected_game.home_team)

    # Get detailed team stats
    away_team_details = team_nerd_details.get(away_team_abbr)
    home_team_details = team_nerd_details.get(home_team_abbr)

    # Get detailed pitcher stats
    away_pitcher_details = None
    home_pitcher_details = None

    if selected_game.away_starter and selected_game.away_starter != "TBD":
        away_pitcher_details = find_pitcher_nerd_stats_fuzzy(
            pitcher_nerd_details, selected_game.away_starter
        )

    if selected_game.home_starter and selected_game.home_starter != "TBD":
        home_pitcher_details = find_pitcher_nerd_stats_fuzzy(
            pitcher_nerd_details, selected_game.home_starter
        )

    # Format the game time in Eastern time
    game_time_et = "TBD"
    if selected_game.game_time and selected_game.game_time != "TBD":
        try:
            # Parse the time - assuming it comes in ISO format with timezone
            game_dt = datetime.fromisoformat(
                selected_game.game_time.replace("Z", "+00:00")
            )
            # Convert to Eastern time
            eastern = pytz.timezone("US/Eastern")
            game_dt_et = game_dt.astimezone(eastern)
            game_time_et = game_dt_et.strftime("%I:%M %p ET").lstrip("0")
        except Exception:
            # If parsing fails, use the original time
            game_time_et = selected_game.game_time

    # Format the game date
    try:
        game_date = datetime.strptime(date, "%Y-%m-%d").strftime("%A, %B %d, %Y")
    except Exception:
        game_date = date

    # Build the complete data dictionary
    data = {
        "away_team": selected_game.away_team,
        "home_team": selected_game.home_team,
        "game_date": game_date,
        "game_time": game_time_et,
        "away_starter": selected_game.away_starter or "TBD",
        "home_starter": selected_game.home_starter or "TBD",
        "gnerd_score": selected_game.gnerd_score,
        "average_team_nerd_score": selected_game.average_team_nerd_score,
        "away_team_nerd_score": selected_game.away_team_nerd_score,
        "home_team_nerd_score": selected_game.home_team_nerd_score,
        "average_pitcher_nerd_score": selected_game.average_pitcher_nerd_score or 0.0,
        "away_pitcher_nerd_score": selected_game.away_pitcher_nerd_score or 0.0,
        "home_pitcher_nerd_score": selected_game.home_pitcher_nerd_score or 0.0,
    }

    # Add away team detailed stats
    if away_team_details:
        team_stats = away_team_details.team_stats
        data.update(
            {
                "away_batting_runs": team_stats.batting_runs,
                "away_barrel_rate": team_stats.barrel_rate,
                "away_baserunning_runs": team_stats.baserunning_runs,
                "away_fielding_runs": team_stats.fielding_runs,
                "away_payroll": team_stats.payroll,
                "away_age": team_stats.age,
                "away_luck": team_stats.luck,
                "away_z_batting_runs": away_team_details.z_batting_runs,
                "away_z_barrel_rate": away_team_details.z_barrel_rate,
                "away_z_baserunning_runs": away_team_details.z_baserunning_runs,
                "away_z_fielding_runs": away_team_details.z_fielding_runs,
                "away_z_payroll": away_team_details.z_payroll,
                "away_z_age": away_team_details.z_age,
                "away_z_luck": away_team_details.z_luck,
            }
        )
    else:
        # Default values if no team data
        data.update(
            {
                "away_batting_runs": 0.0,
                "away_barrel_rate": 0.0,
                "away_baserunning_runs": 0.0,
                "away_fielding_runs": 0.0,
                "away_payroll": 0.0,
                "away_age": 0.0,
                "away_luck": 0.0,
                "away_z_batting_runs": 0.0,
                "away_z_barrel_rate": 0.0,
                "away_z_baserunning_runs": 0.0,
                "away_z_fielding_runs": 0.0,
                "away_z_payroll": 0.0,
                "away_z_age": 0.0,
                "away_z_luck": 0.0,
            }
        )

    # Add home team detailed stats
    if home_team_details:
        team_stats = home_team_details.team_stats
        data.update(
            {
                "home_batting_runs": team_stats.batting_runs,
                "home_barrel_rate": team_stats.barrel_rate,
                "home_baserunning_runs": team_stats.baserunning_runs,
                "home_fielding_runs": team_stats.fielding_runs,
                "home_payroll": team_stats.payroll,
                "home_age": team_stats.age,
                "home_luck": team_stats.luck,
                "home_z_batting_runs": home_team_details.z_batting_runs,
                "home_z_barrel_rate": home_team_details.z_barrel_rate,
                "home_z_baserunning_runs": home_team_details.z_baserunning_runs,
                "home_z_fielding_runs": home_team_details.z_fielding_runs,
                "home_z_payroll": home_team_details.z_payroll,
                "home_z_age": home_team_details.z_age,
                "home_z_luck": home_team_details.z_luck,
            }
        )
    else:
        # Default values if no team data
        data.update(
            {
                "home_batting_runs": 0.0,
                "home_barrel_rate": 0.0,
                "home_baserunning_runs": 0.0,
                "home_fielding_runs": 0.0,
                "home_payroll": 0.0,
                "home_age": 0.0,
                "home_luck": 0.0,
                "home_z_batting_runs": 0.0,
                "home_z_barrel_rate": 0.0,
                "home_z_baserunning_runs": 0.0,
                "home_z_fielding_runs": 0.0,
                "home_z_payroll": 0.0,
                "home_z_age": 0.0,
                "home_z_luck": 0.0,
            }
        )

    # Add away pitcher detailed stats
    if away_pitcher_details:
        pitcher_stats = away_pitcher_details.pitcher_stats
        data.update(
            {
                "away_xfip_minus": pitcher_stats.xfip_minus,
                "away_swinging_strike_rate": pitcher_stats.swinging_strike_rate,
                "away_strike_rate": pitcher_stats.strike_rate,
                "away_velocity": pitcher_stats.velocity,
                "away_pitcher_age": pitcher_stats.age,
                "away_pace": pitcher_stats.pace,
                "away_luck_pitcher": pitcher_stats.luck,
                "away_knuckleball_rate": pitcher_stats.knuckleball_rate,
                "away_z_xfip_minus": away_pitcher_details.z_xfip_minus,
                "away_z_swinging_strike_rate": away_pitcher_details.z_swinging_strike_rate,
                "away_z_strike_rate": away_pitcher_details.z_strike_rate,
                "away_z_velocity": away_pitcher_details.z_velocity,
                "away_z_pitcher_age": away_pitcher_details.z_age,
                "away_z_pace": away_pitcher_details.z_pace,
            }
        )
        # Add formatted pitcher stats section
        data[
            "away_pitcher_stats_section"
        ] = f"""- xFIP-: {pitcher_stats.xfip_minus:.0f} (z-score: {away_pitcher_details.z_xfip_minus:.2f})
- Swinging Strike Rate: {pitcher_stats.swinging_strike_rate:.3f} (z-score:
  {away_pitcher_details.z_swinging_strike_rate:.2f})
- Strike Rate: {pitcher_stats.strike_rate:.3f} (z-score: {away_pitcher_details.z_strike_rate:.2f})
- Velocity: {pitcher_stats.velocity:.1f} mph (z-score: {away_pitcher_details.z_velocity:.2f})
- Age: {pitcher_stats.age} (z-score: {away_pitcher_details.z_age:.2f})
- Pace: {pitcher_stats.pace:.1f}s (z-score: {away_pitcher_details.z_pace:.2f})
- Luck (ERA- minus xFIP-): {pitcher_stats.luck:.1f}
- Knuckleball Rate: {pitcher_stats.knuckleball_rate:.3f}"""
    else:
        # Default values if no pitcher data
        data.update(
            {
                "away_xfip_minus": 0,
                "away_swinging_strike_rate": 0.0,
                "away_strike_rate": 0.0,
                "away_velocity": 0.0,
                "away_pitcher_age": 0,
                "away_pace": 0.0,
                "away_luck_pitcher": 0.0,
                "away_knuckleball_rate": 0.0,
                "away_z_xfip_minus": 0.0,
                "away_z_swinging_strike_rate": 0.0,
                "away_z_strike_rate": 0.0,
                "away_z_velocity": 0.0,
                "away_z_pitcher_age": 0.0,
                "away_z_pace": 0.0,
            }
        )
        # Add no data message
        data["away_pitcher_stats_section"] = (
            "No pNERD data, likely because the pitcher hasn't met the minimum thresholds for inclusion."
        )

    # Add home pitcher detailed stats
    if home_pitcher_details:
        pitcher_stats = home_pitcher_details.pitcher_stats
        data.update(
            {
                "home_xfip_minus": pitcher_stats.xfip_minus,
                "home_swinging_strike_rate": pitcher_stats.swinging_strike_rate,
                "home_strike_rate": pitcher_stats.strike_rate,
                "home_velocity": pitcher_stats.velocity,
                "home_pitcher_age": pitcher_stats.age,
                "home_pace": pitcher_stats.pace,
                "home_luck_pitcher": pitcher_stats.luck,
                "home_knuckleball_rate": pitcher_stats.knuckleball_rate,
                "home_z_xfip_minus": home_pitcher_details.z_xfip_minus,
                "home_z_swinging_strike_rate": home_pitcher_details.z_swinging_strike_rate,
                "home_z_strike_rate": home_pitcher_details.z_strike_rate,
                "home_z_velocity": home_pitcher_details.z_velocity,
                "home_z_pitcher_age": home_pitcher_details.z_age,
                "home_z_pace": home_pitcher_details.z_pace,
            }
        )
        # Add formatted pitcher stats section
        data[
            "home_pitcher_stats_section"
        ] = f"""- xFIP-: {pitcher_stats.xfip_minus:.0f} (z-score: {home_pitcher_details.z_xfip_minus:.2f})
- Swinging Strike Rate: {pitcher_stats.swinging_strike_rate:.3f} (z-score:
  {home_pitcher_details.z_swinging_strike_rate:.2f})
- Strike Rate: {pitcher_stats.strike_rate:.3f} (z-score: {home_pitcher_details.z_strike_rate:.2f})
- Velocity: {pitcher_stats.velocity:.1f} mph (z-score: {home_pitcher_details.z_velocity:.2f})
- Age: {pitcher_stats.age} (z-score: {home_pitcher_details.z_age:.2f})
- Pace: {pitcher_stats.pace:.1f}s (z-score: {home_pitcher_details.z_pace:.2f})
- Luck (ERA- minus xFIP-): {pitcher_stats.luck:.1f}
- Knuckleball Rate: {pitcher_stats.knuckleball_rate:.3f}"""
    else:
        # Default values if no pitcher data
        data.update(
            {
                "home_xfip_minus": 0,
                "home_swinging_strike_rate": 0.0,
                "home_strike_rate": 0.0,
                "home_velocity": 0.0,
                "home_pitcher_age": 0,
                "home_pace": 0.0,
                "home_luck_pitcher": 0.0,
                "home_knuckleball_rate": 0.0,
                "home_z_xfip_minus": 0.0,
                "home_z_swinging_strike_rate": 0.0,
                "home_z_strike_rate": 0.0,
                "home_z_velocity": 0.0,
                "home_z_pitcher_age": 0.0,
                "home_z_pace": 0.0,
            }
        )
        # Add no data message
        data["home_pitcher_stats_section"] = (
            "No pNERD data, likely because the pitcher hasn't met the minimum thresholds for inclusion."
        )

    return data


def main() -> None:
    """Main function to generate the game prompt."""
    parser = argparse.ArgumentParser(
        description="Generate a game summary prompt with NERD scores and statistics"
    )
    parser.add_argument(
        "date",
        nargs="?",
        default="2025-07-23",
        help="Date in YYYY-MM-DD format (default: 2025-07-23)",
    )
    parser.add_argument(
        "game_index",
        nargs="?",
        type=int,
        default=0,
        help="Index of the game to use (0-based, default: 0 for first game)",
    )

    args = parser.parse_args()

    # Use the project_root that was already calculated during imports
    template_file = (
        project_root / "src" / "mlb_watchability" / "prompt-game-summary-template.md"
    )
    output_file = (
        Path.cwd() / f"game_prompt_{args.date}_game_{args.game_index}.md"
    )  # Include date and game index

    # Read template
    template = template_file.read_text()

    # Get game data using actual MLB data (use 2025 season by default)
    season = 2025
    print(
        f"Starting game prompt generation for {args.date}, game index {args.game_index}..."
    )
    try:
        game_data = get_game_data(
            date=args.date, season=season, game_index=args.game_index
        )
    except Exception as e:
        print(f"Error getting game data: {e}")
        print(
            "This might be because there are no games on that date, the APIs are unavailable, or the game index is invalid."
        )
        return

    # Populate template
    print("Generating prompt from template...")
    populated_prompt = template.format(**game_data)

    # Write output
    output_file.write_text(populated_prompt)

    print(
        f"Generated game prompt for {game_data['away_team']} @ {game_data['home_team']} (game index {args.game_index})"
    )
    print(f"Output written to: {output_file}")
    print(f"gNERD Score: {game_data['gnerd_score']:.2f}")
    print(
        f"Team NERDs: {game_data['away_team_nerd_score']:.2f} (away) + {game_data['home_team_nerd_score']:.2f} (home)"
    )
    print(
        f"Pitcher NERDs: {game_data['away_pitcher_nerd_score']:.2f} (away) + {game_data['home_pitcher_nerd_score']:.2f} (home)"
    )


if __name__ == "__main__":
    main()
