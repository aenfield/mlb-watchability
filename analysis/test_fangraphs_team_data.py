#!/usr/bin/env python3
"""Quick script to fetch and save raw team batting data from Fangraphs via pybaseball."""

import pybaseball as pb


def main():
    """Fetch team batting data from Fangraphs and save to CSV."""
    print("Fetching team batting data from Fangraphs for 2025...")
    
    # Get team batting data for 2025
    team_data = pb.team_batting(2025)
    
    # Save to CSV
    output_file = "team_batting_fangraphs_raw_data.csv"
    team_data.to_csv(output_file, index=False)
    
    print(f"✓ Saved {len(team_data)} team records to {output_file}")
    print(f"✓ Columns: {list(team_data.columns)}")


if __name__ == "__main__":
    main()