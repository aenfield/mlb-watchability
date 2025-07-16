"""Data retrieval module for MLB Watchability."""

import zoneinfo
from datetime import datetime
from typing import Any

import pandas as pd
import pybaseball as pb
import statsapi  # type: ignore

from .pitcher_stats import PitcherStats


def get_game_schedule(date: str) -> list[dict[str, Any]]:
    """
    Retrieve the game schedule for a given date.

    Args:
        date: Date in YYYY-MM-DD format

    Returns:
        List of games with team information and starting pitchers

    Raises:
        ValueError: If date format is invalid
        RuntimeError: If API call fails
    """
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(
            f"Invalid date format. Expected YYYY-MM-DD, got: {date}"
        ) from e

    try:
        # Convert YYYY-MM-DD to MM/DD/YYYY format for MLB-StatsAPI
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        api_date = date_obj.strftime("%m/%d/%Y")

        # Fetch schedule data from MLB-StatsAPI
        schedule_data = statsapi.schedule(start_date=api_date, end_date=api_date)

        # Convert to our expected format
        games = []
        for game in schedule_data:
            # Extract starting pitcher info if available
            away_starter = game.get("away_probable_pitcher") or None
            home_starter = game.get("home_probable_pitcher") or None

            # Format game time if available, convert to Eastern time
            game_time = None
            if "game_datetime" in game:
                try:
                    # Parse UTC datetime
                    game_datetime = game["game_datetime"]
                    if game_datetime.endswith("Z"):
                        # Parse as UTC
                        utc_dt = datetime.strptime(game_datetime, "%Y-%m-%dT%H:%M:%SZ")
                        utc_dt = utc_dt.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
                    else:
                        # Try with timezone info
                        utc_dt = datetime.fromisoformat(
                            game_datetime.replace("Z", "+00:00")
                        )

                    # Convert to Eastern time
                    eastern_tz = zoneinfo.ZoneInfo("America/New_York")
                    eastern_dt = utc_dt.astimezone(eastern_tz)
                    game_time = eastern_dt.strftime("%H:%M")
                except (ValueError, TypeError):
                    game_time = None

            game_dict = {
                "date": date,
                "away_team": game.get("away_name", ""),
                "home_team": game.get("home_name", ""),
                "time": game_time,
                "away_starter": away_starter,
                "home_starter": home_starter,
            }
            games.append(game_dict)

    except Exception as e:
        raise RuntimeError(
            f"Failed to retrieve game schedule for {date}: {str(e)}"
        ) from e
    else:
        return games


def get_all_pitcher_stats(season: int = 2024) -> dict[str, PitcherStats]:
    """
    Retrieve pitcher statistics for all starting pitchers using pybaseball.

    Args:
        season: Season year (default: 2024)

    Returns:
        Dictionary mapping pitcher names to PitcherStats objects

    Raises:
        RuntimeError: If API call fails or data retrieval fails
    """
    try:
        # Fetch pitcher statistics for the season
        # Using qual=20 to get starting pitchers with at least 20 innings pitched
        pitcher_stats_df = pb.pitching_stats(season, qual=20)

        # Filter for starting pitchers only (pitchers with at least 1 game started)
        starting_pitchers = pitcher_stats_df[pitcher_stats_df["GS"] > 0]

        pitcher_stats_dict = {}

        for _, pitcher_row in starting_pitchers.iterrows():
            # Calculate Strike Rate from Strikes/Pitches
            strike_rate = pitcher_row["Strikes"] / pitcher_row["Pitches"]

            # Calculate Luck (ERA- minus xFIP-)
            luck = pitcher_row["ERA-"] - pitcher_row["xFIP-"]

            # Handle KN% NaN values by setting to 0
            kn_rate = pitcher_row.get("KN%", 0.0)
            if pd.isna(kn_rate):
                kn_rate = 0.0

            # Use FBv for velocity as it has better coverage
            velocity = pitcher_row["FBv"]

            # Create PitcherStats object
            pitcher_stats = PitcherStats(
                name=pitcher_row["Name"],
                team=pitcher_row["Team"],
                xfip_minus=pitcher_row["xFIP-"],
                swinging_strike_rate=pitcher_row["SwStr%"],
                strike_rate=strike_rate,
                velocity=velocity,
                age=pitcher_row["Age"],
                pace=pitcher_row["Pace"],
                luck=luck,
                knuckleball_rate=kn_rate,
            )

            pitcher_stats_dict[pitcher_row["Name"]] = pitcher_stats

    except Exception as e:
        raise RuntimeError(
            f"Failed to retrieve pitcher statistics for season {season}: {str(e)}"
        ) from e
    else:
        return pitcher_stats_dict
