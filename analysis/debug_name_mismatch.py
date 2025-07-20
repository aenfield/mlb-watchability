#!/usr/bin/env python3

# Debug script to find name mismatches between game schedule and pitcher stats
# ruff: skip-file
# type: ignore

import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mlb_watchability.data_retrieval import get_game_schedule
from mlb_watchability.game_scores import find_pitcher_score
from mlb_watchability.pitcher_stats import calculate_detailed_pitcher_nerd_scores


def debug_name_mismatch():
    """Debug name mismatches between game schedule and pitcher stats."""

    print("Debugging Name Mismatches")
    print("=" * 40)

    try:
        # Get today's games (using a date we know has games)
        print("Getting game schedule for 2025-07-18...")
        games = get_game_schedule("2025-07-18")

        # Get pitcher NERD scores
        print("Getting pitcher NERD scores...")
        pitcher_nerd_details = calculate_detailed_pitcher_nerd_scores(2025)
        pitcher_nerd_scores = {
            pitcher: nerd_stats.pnerd_score
            for pitcher, nerd_stats in pitcher_nerd_details.items()
        }

        # Extract all pitcher names from games
        game_pitchers = set()
        for game in games:
            away_starter = game.get("away_starter")
            home_starter = game.get("home_starter")
            if away_starter and away_starter != "TBD":
                game_pitchers.add(away_starter)
            if home_starter and home_starter != "TBD":
                game_pitchers.add(home_starter)

        print(f"Found {len(game_pitchers)} unique pitchers in game schedule")
        print(f"Found {len(pitcher_nerd_scores)} pitchers with NERD scores")
        print()

        # Check for exact matches and fuzzy matches
        exact_matches = []
        fuzzy_matches = []
        missing_pitchers = []

        for game_pitcher in game_pitchers:
            if game_pitcher in pitcher_nerd_scores:
                exact_matches.append(game_pitcher)
            else:
                # Try fuzzy matching
                fuzzy_score = find_pitcher_score(game_pitcher, pitcher_nerd_scores)
                if fuzzy_score is not None:
                    fuzzy_matches.append((game_pitcher, fuzzy_score))
                else:
                    missing_pitchers.append(game_pitcher)

        print(f"Exact matches: {len(exact_matches)}")
        print(f"Fuzzy matches: {len(fuzzy_matches)}")
        print(f"Still missing: {len(missing_pitchers)}")
        print()

        # Show fuzzy matches
        if fuzzy_matches:
            print("FUZZY MATCHES (resolved by name normalization):")
            print("-" * 50)
            for game_name, score in fuzzy_matches:
                print(f"  '{game_name}' -> pNERD: {score:.1f}")
            print()

        # Show missing pitchers and try to find similar names
        if missing_pitchers:
            print("MISSING PITCHERS (not found in NERD scores):")
            print("-" * 50)

            for missing in missing_pitchers:
                print(f"\nGame schedule: '{missing}'")

                # Try to find similar names in pitcher NERD scores
                # Split the missing name and look for partial matches
                missing_parts = missing.lower().split()
                candidates = []

                for pnerd_pitcher in pitcher_nerd_scores:
                    pnerd_parts = pnerd_pitcher.lower().split()

                    # Check if last names match
                    if missing_parts and pnerd_parts:
                        if (
                            missing_parts[-1] == pnerd_parts[-1]
                            or missing_parts[0] == pnerd_parts[0]
                        ):  # Last name match
                            candidates.append(pnerd_pitcher)

                if candidates:
                    print("  Possible matches in NERD data:")
                    for candidate in candidates:
                        score = pitcher_nerd_scores[candidate]
                        print(f"    '{candidate}' (pNERD: {score:.1f})")
                else:
                    print("  No similar names found in NERD data")

        # Show some examples of successful matches
        print("\nSuccessful matches (first 10):")
        for match in exact_matches[:10]:
            score = pitcher_nerd_scores[match]
            print(f"  '{match}' (pNERD: {score:.1f})")

        # Focus on the Jacob/Jake Latz case specifically
        print("\nSpecific check for Latz:")
        latz_in_games = [p for p in game_pitchers if "latz" in p.lower()]
        latz_in_nerd = [p for p in pitcher_nerd_scores if "latz" in p.lower()]

        print(f"  Game schedule has: {latz_in_games}")
        print(f"  NERD scores has: {latz_in_nerd}")

        if latz_in_nerd:
            for latz_pitcher in latz_in_nerd:
                score = pitcher_nerd_scores[latz_pitcher]
                print(f"    '{latz_pitcher}' has pNERD score: {score:.1f}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_name_mismatch()
