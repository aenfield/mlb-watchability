#!/usr/bin/env python3
"""Quick test script for MLB-StatsAPI library."""

import statsapi  # type: ignore


def main() -> None:

    # Test 1: Basic schedule query
    print("\n=== Test 1: Schedule for a specific date ===")
    # date = "2025-07-13"
    date = "2025-07-18"

    try:
        sched = statsapi.schedule(start_date=date, end_date=date)
        print(f"Schedule for {date}:")
        print(f"Type: {type(sched)}")
        if isinstance(sched, list):
            print(f"Found {len(sched)} games")
            if sched:
                print("First game:")
                print(sched[0])
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
