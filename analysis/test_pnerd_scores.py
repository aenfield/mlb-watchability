#!/usr/bin/env python3

# skip linting and typing checks since this is a quickie script for understanding the data and API
# ruff: skip-file
# type: ignore
"""Quickie script to generate pNERD scores for all pitchers and export to CSV."""

import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd

from mlb_watchability.pitcher_stats import calculate_detailed_pitcher_nerd_scores


def generate_pnerd_scores_csv():
    """Generate pNERD scores for all pitchers and export to CSV."""

    print("Generating pNERD Scores for All Pitchers")
    print("=" * 50)

    try:
        # Calculate detailed pitcher NERD scores (defaults to 2025 season)
        print("Calculating detailed pitcher NERD scores...")
        pitcher_nerd_details = calculate_detailed_pitcher_nerd_scores(2025)

        print(f"Retrieved pNERD scores for {len(pitcher_nerd_details)} pitchers")
        print()

        # Convert to DataFrame for easy CSV export
        export_data = []

        for pitcher_name, nerd_stats in pitcher_nerd_details.items():
            # Extract all data from PitcherNerdStats and PitcherStats
            pitcher_stats = nerd_stats.pitcher_stats

            row = {
                # Basic pitcher info
                "Name": pitcher_name,
                "Team": pitcher_stats.team,
                # Raw statistics from PitcherStats
                "xfip_minus": pitcher_stats.xfip_minus,
                "swinging_strike_rate": pitcher_stats.swinging_strike_rate,
                "strike_rate": pitcher_stats.strike_rate,
                "velocity": pitcher_stats.velocity,
                "age": pitcher_stats.age,
                "pace": pitcher_stats.pace,
                "luck": pitcher_stats.luck,
                "knuckleball_rate": pitcher_stats.knuckleball_rate,
                # Z-scores and adjustments from PitcherNerdStats
                "z_xfip_minus": nerd_stats.z_xfip_minus,
                "z_swinging_strike_rate": nerd_stats.z_swinging_strike_rate,
                "z_strike_rate": nerd_stats.z_strike_rate,
                "adjusted_velocity": nerd_stats.adjusted_velocity,
                "adjusted_age": nerd_stats.adjusted_age,
                "z_pace": nerd_stats.z_pace,
                "adjusted_luck": nerd_stats.adjusted_luck,
                # Final pNERD score
                "pnerd_score": nerd_stats.pnerd_score,
            }

            export_data.append(row)

        # Create DataFrame and sort by pNERD score (highest first)
        df = pd.DataFrame(export_data)
        df = df.sort_values("pnerd_score", ascending=False)

        print("pNERD Score Summary:")
        print(f"  Highest pNERD: {df['pnerd_score'].max():.1f} ({df.iloc[0]['Name']})")
        print(f"  Lowest pNERD: {df['pnerd_score'].min():.1f} ({df.iloc[-1]['Name']})")
        print(f"  Average pNERD: {df['pnerd_score'].mean():.1f}")
        print(f"  Median pNERD: {df['pnerd_score'].median():.1f}")
        print()

        # Show top 10 pitchers
        print("Top 10 pitchers by pNERD score:")
        top_10 = df[["Name", "Team", "pnerd_score"]].head(10)
        for i, row in top_10.iterrows():
            print(f"  {row['Name']} ({row['Team']}): {row['pnerd_score']:.1f}")
        print()

        # Create analysis directory if it doesn't exist
        analysis_dir = Path("analysis")
        analysis_dir.mkdir(exist_ok=True)

        # Export to CSV
        csv_filename = analysis_dir / "pnerd_scores_export.csv"

        df.to_csv(csv_filename, index=False)
        print(f"✓ CSV exported successfully: {csv_filename}")
        print(f"  Exported {len(df)} pitchers")
        print(f"  Exported {len(df.columns)} columns")

        # Show column summary
        print("\nExported columns:")
        for col in df.columns:
            print(f"  {col}")

        return df

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    generate_pnerd_scores_csv()
