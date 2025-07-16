"""Data retrieval module for MLB Watchability."""

import zoneinfo
from datetime import datetime
from typing import Any

import statsapi  # type: ignore


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
