#!/usr/bin/env python3
"""Quick test script for MLB-StatsAPI library."""

from datetime import datetime
from typing import Any

import pandas as pd
import statsapi  # type: ignore


def format_time_edt(iso_datetime: str) -> str:
    """Convert ISO datetime to EDT format like '07:35p'."""
    try:
        # Parse the ISO datetime (assuming UTC)
        dt = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))

        # Convert to EDT (UTC-4)
        edt_dt = dt.replace(tzinfo=None) - pd.Timedelta(hours=4)

        # Format as requested
        hour = edt_dt.hour
        minute = edt_dt.minute

        # Convert to 12-hour format
        NOON_MIDNIGHT = 12
        if hour == 0:
            hour_12 = NOON_MIDNIGHT
            ampm = "a"
        elif hour < NOON_MIDNIGHT:
            hour_12 = hour
            ampm = "a"
        elif hour == NOON_MIDNIGHT:
            hour_12 = NOON_MIDNIGHT
            ampm = "p"
        else:
            hour_12 = hour - NOON_MIDNIGHT
            ampm = "p"
    except Exception:
        return ""
    else:
        return f"{hour_12:02d}:{minute:02d}{ampm}"


def extract_game_info(games: list[dict[str, Any]]) -> pd.DataFrame:
    """Extract key game information and return as DataFrame."""
    game_data = []

    for game in games:
        # Format game time in EDT
        game_time_edt = format_time_edt(game.get("game_datetime", ""))

        # Extract basic game information
        game_info = {
            "game_date": game.get("game_date", ""),
            "game_time": game_time_edt,
            "away_team": game.get("away_name", ""),
            "home_team": game.get("home_name", ""),
            "away_score": game.get("away_score", ""),
            "home_score": game.get("home_score", ""),
            "inning": game.get("current_inning", ""),
            "inning_state": game.get("inning_state", ""),
            "away_probable_pitcher": game.get("away_probable_pitcher", ""),
            "home_probable_pitcher": game.get("home_probable_pitcher", ""),
        }

        game_data.append(game_info)

    return pd.DataFrame(game_data)


def main() -> None:

    # Test 1: Basic schedule query
    print("\n=== Test 1: Schedule for a specific date ===")
    # date = "2025-07-13"
    date = "2025-07-21"

    try:
        sched = statsapi.schedule(start_date=date, end_date=date)
        print(f"Schedule for {date}:")
        print(f"Type: {type(sched)}")
        if isinstance(sched, list):
            print(f"Found {len(sched)} games")
            if sched:
                print("First game:")
                print(sched[0])

                # Extract game information and create DataFrame
                print("\n=== Extracting game information ===")
                games_df = extract_game_info(sched)
                print(f"Created DataFrame with {len(games_df)} games")
                print("\nGame summary:")
                print(games_df.to_string(index=False))

                # Save to CSV
                csv_filename = f"mlb_games_{date}.csv"
                games_df.to_csv(csv_filename, index=False)
                print(f"\nSaved game data to {csv_filename}")
        else:
            print("Raw response:")
            print(sched)
    except Exception as e:
        print(f"Error getting schedule: {e}")

    # Test 2: Schedule with team filter
    print("\n=== Test 2: Schedule for Yankees ===")
    try:
        # Yankees team ID is typically 147
        sched = statsapi.schedule(start_date=date, end_date=date, team=147)
        print("Yankees schedule:")
        print(f"Type: {type(sched)}")
        if isinstance(sched, list):
            print(f"Found {len(sched)} games")
            if sched:
                print("Game details:")
                for game in sched:
                    print(game)
        else:
            print("Raw response:")
            print(sched)
    except Exception as e:
        print(f"Error getting Yankees schedule: {e}")

    # Test 3: Lookup teams to get team IDs
    print("\n=== Test 3: Team lookup ===")
    try:
        teams = statsapi.lookup_team("yankees")
        print(f"Yankees lookup result: {teams}")
    except Exception as e:
        print(f"Error looking up teams: {e}")

    # Test 4: Get a specific game's boxscore
    print("\n=== Test 4: Boxscore example ===")
    try:
        # Try to get a recent game
        recent_sched = statsapi.schedule(start_date=date, end_date=date)
        if isinstance(recent_sched, list) and recent_sched:
            game = recent_sched[0]
            print(f"Game found: {game}")

            # Try to get boxscore if game has an ID
            if isinstance(game, dict) and "game_id" in game:
                boxscore = statsapi.boxscore(game["game_id"])
                print(f"Boxscore type: {type(boxscore)}")
                if isinstance(boxscore, str):
                    print(f"Boxscore length: {len(boxscore)} characters")
                    print(f"First 500 chars: {boxscore[:500]}")
                else:
                    print(f"Boxscore: {boxscore}")
        else:
            print("No games found for boxscore test")
    except Exception as e:
        print(f"Error getting boxscore: {e}")

    # Test 5: Player lookup
    print("\n=== Test 5: Player lookup ===")
    try:
        players = statsapi.lookup_player("Gerrit Cole")
        print(f"Gerrit Cole lookup: {players}")
    except Exception as e:
        print(f"Error looking up player: {e}")

    print("\n=== Library exploration complete ===")


if __name__ == "__main__":
    main()
