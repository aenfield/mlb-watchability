#!/usr/bin/env python3
"""Quick test script to call pybaseball team_pitching functions and save to CSV."""

import sys
import pybaseball as pyb


def main() -> None:
    print(
        f"pybaseball version: {pyb.__version__ if hasattr(pyb, '__version__') else 'unknown'}"
    )
    print(f"pybaseball location: {pyb.__file__}")
    print()
    # Get command line argument, default to 'all'
    pitching_type = sys.argv[1] if len(sys.argv) > 1 else "all"

    if pitching_type == "all":
        team_pitching_data = pyb.team_pitching(2025)
        output_file = "analysis/team_pitching_all_2025.csv"
    elif pitching_type == "sta":
        team_pitching_data = pyb.team_pitching_starters(2025)
        output_file = "analysis/team_pitching_starters_2025.csv"
    elif pitching_type == "rel":
        team_pitching_data = pyb.team_pitching_relievers(2025)
        output_file = "analysis/team_pitching_relievers_2025.csv"
    else:
        print(f"Invalid argument: {pitching_type}. Use 'all', 'sta', or 'rel'")
        sys.exit(1)

    # Save to CSV
    team_pitching_data.to_csv(output_file, index=False)
    print(f"Team pitching data ({pitching_type}) saved to {output_file}")
    print(f"Shape: {team_pitching_data.shape}")


if __name__ == "__main__":
    main()
