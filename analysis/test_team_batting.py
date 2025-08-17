#!/usr/bin/env python3
"""Quick test script to call pybaseball team_batting function and save to CSV."""

import sys
import pybaseball as pyb


def main() -> None:
    print(
        f"pybaseball version: {pyb.__version__ if hasattr(pyb, '__version__') else 'unknown'}"
    )
    print(f"pybaseball location: {pyb.__file__}")
    print()
    
    # Get command line argument for season, default to 2025
    season = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    
    print(f"Fetching team batting data for {season}...")
    team_batting_data = pyb.team_batting(season)
    output_file = f"analysis/team_batting_{season}.csv"

    # Save to CSV
    team_batting_data.to_csv(output_file, index=False)
    print(f"Team batting data saved to {output_file}")
    print(f"Shape: {team_batting_data.shape}")
    print(f"Columns: {len(team_batting_data.columns)}")
    print(f"Teams: {len(team_batting_data['Team'].unique())}")


if __name__ == "__main__":
    main()