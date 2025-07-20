#!/usr/bin/env python3

# Test script for fuzzy name matching
# ruff: skip-file
# type: ignore

import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mlb_watchability.game_scores import find_pitcher_score, normalize_pitcher_name


def test_fuzzy_matching():
    """Test fuzzy name matching for pitcher names."""

    print("Testing Fuzzy Pitcher Name Matching")
    print("=" * 40)

    # Mock pitcher NERD scores dictionary (like what we have)
    mock_pitcher_scores = {
        "Jake Latz": 4.2,
        "Jesus Luzardo": 4.3,
        "Mike Soroka": 3.9,
        "Chris Sale": 5.1,
        "Matt Waldron": 2.5,  # Let's pretend he's in there
    }

    # Test cases - names as they might appear in game schedule
    test_cases = [
        "Jacob Latz",  # Should match "Jake Latz"
        "Jesús Luzardo",  # Should match "Jesus Luzardo" (accent removed)
        "Michael Soroka",  # Should match "Mike Soroka"
        "Christopher Sale",  # Should match "Chris Sale"
        "Matthew Waldron",  # Should match "Matt Waldron"
        "Paul Skenes",  # Should not match (not in mock data)
        "Jake Latz",  # Should match exactly
    ]

    print("Test Cases:")
    print("-" * 20)

    for game_name in test_cases:
        score = find_pitcher_score(game_name, mock_pitcher_scores)
        print(f"Game schedule: '{game_name}'")

        if score is not None:
            # Find which name it matched
            normalized_game = normalize_pitcher_name(game_name)
            matched_name = None
            for pnerd_name in mock_pitcher_scores:
                if normalize_pitcher_name(pnerd_name) == normalized_game:
                    matched_name = pnerd_name
                    break

            print(f"  ✓ Matched: '{matched_name}' (score: {score:.1f})")
            print(f"  Normalized: '{game_name}' -> '{normalized_game}'")
        else:
            print("  ✗ No match found")
        print()

    # Test normalization function directly
    print("Normalization Examples:")
    print("-" * 25)

    normalization_tests = [
        "Jacob Latz",
        "Jesús Luzardo",
        "Michael Soroka",
        "Christopher Sale",
        "Matthew Waldron",
    ]

    for name in normalization_tests:
        normalized = normalize_pitcher_name(name)
        print(f"'{name}' -> '{normalized}'")

    print()
    print("Real-world test with actual data:")
    print("-" * 35)

    # Test with actual pitcher data
    try:
        from mlb_watchability.pitcher_stats import (
            calculate_detailed_pitcher_nerd_scores,
        )

        pitcher_nerd_details = calculate_detailed_pitcher_nerd_scores(2025)
        real_pitcher_scores = {
            pitcher: nerd_stats.pnerd_score
            for pitcher, nerd_stats in pitcher_nerd_details.items()
        }

        # Test the Jacob Latz case specifically
        jacob_score = find_pitcher_score("Jacob Latz", real_pitcher_scores)
        jake_score = find_pitcher_score("Jake Latz", real_pitcher_scores)

        print(f"'Jacob Latz' lookup result: {jacob_score}")
        print(f"'Jake Latz' lookup result: {jake_score}")

        if jacob_score is not None:
            print("✓ Jacob Latz now resolves to a score!")
        else:
            print("✗ Jacob Latz still not found")

        # Test other common mismatches
        test_real_names = [
            "Jesús Luzardo",
            "Michael Soroka",
            "Jesus Luzardo",
            "Mike Soroka",
        ]

        print("\nOther name matching tests:")
        for name in test_real_names:
            score = find_pitcher_score(name, real_pitcher_scores)
            status = "✓" if score is not None else "✗"
            score_str = f"{score:.1f}" if score is not None else "No match"
            print(f"  {status} '{name}': {score_str}")

    except Exception as e:
        print(f"Error testing with real data: {e}")


if __name__ == "__main__":
    test_fuzzy_matching()
