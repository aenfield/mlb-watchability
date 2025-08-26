#!/usr/bin/env python3
"""
Pitcher pNERD Analysis Script

Calculates pNERD scores for all starting pitchers (with at least one game started and 20+ innings pitched)
and outputs a comprehensive CSV with pitcher name, team, total pNERD score, raw statistics, z-scores, and component breakdown.
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd

from mlb_watchability.pitcher_stats import calculate_detailed_pitcher_nerd_scores


def generate_comprehensive_pnerd_analysis(season: int = 2025) -> None:
    """
    Generate comprehensive pNERD analysis for all pitchers and export to CSV.
    
    Args:
        season: Season year (default: 2025)
    """
    print("Comprehensive Pitcher pNERD Analysis")
    print("=" * 50)
    print(f"Season: {season}")
    print()

    try:
        # Calculate detailed pitcher NERD scores
        print("Calculating detailed pitcher NERD scores...")
        pitcher_nerd_details = calculate_detailed_pitcher_nerd_scores(season)

        print(f"Retrieved pNERD scores for {len(pitcher_nerd_details)} pitchers")
        print("(Filtered to starting pitchers with 1+ GS and 20+ IP)")
        print()

        # Convert to comprehensive DataFrame
        export_data = []

        for pitcher_name, nerd_stats in pitcher_nerd_details.items():
            # Extract all data from PitcherNerdStats and PitcherStats
            pitcher_stats = nerd_stats.pitcher_stats

            row = {
                # Basic pitcher info
                "name": pitcher_name,
                "team": pitcher_stats.team,
                
                # Total pNERD score
                "pnerd_score": nerd_stats.pnerd_score,
                
                # Raw statistics
                "raw_xfip_minus": pitcher_stats.xfip_minus,
                "raw_swinging_strike_rate": pitcher_stats.swinging_strike_rate,
                "raw_strike_rate": pitcher_stats.strike_rate,
                "raw_velocity": pitcher_stats.velocity,
                "raw_age": pitcher_stats.age,
                "raw_pace": pitcher_stats.pace,
                "raw_luck": pitcher_stats.luck,
                "raw_knuckleball_rate": pitcher_stats.knuckleball_rate,
                
                # Z-scores
                "z_xfip_minus": nerd_stats.z_xfip_minus,
                "z_swinging_strike_rate": nerd_stats.z_swinging_strike_rate,
                "z_strike_rate": nerd_stats.z_strike_rate,
                "z_velocity": nerd_stats.z_velocity,
                "z_age": nerd_stats.z_age,
                "z_pace": nerd_stats.z_pace,
                
                # Adjusted values (after caps and rules)
                "adjusted_velocity": nerd_stats.adjusted_velocity,
                "adjusted_age": nerd_stats.adjusted_age,
                "adjusted_luck": nerd_stats.adjusted_luck,
                
                # pNERD formula components
                "component_xfip": nerd_stats.xfip_component,
                "component_swinging_strike": nerd_stats.swinging_strike_component,
                "component_strike_rate": nerd_stats.strike_component,
                "component_velocity": nerd_stats.velocity_component,
                "component_age": nerd_stats.age_component,
                "component_pace": nerd_stats.pace_component,
                "component_luck": nerd_stats.luck_component,
                "component_knuckleball": nerd_stats.knuckleball_component,
                "component_constant": nerd_stats.constant_component,
            }

            export_data.append(row)

        # Create DataFrame and sort by pNERD score (highest first)
        df = pd.DataFrame(export_data)
        df = df.sort_values("pnerd_score", ascending=False)

        # Display summary statistics
        print("pNERD Score Summary:")
        print(f"  Highest pNERD: {df['pnerd_score'].max():.2f} ({df.iloc[0]['name']})")
        print(f"  Lowest pNERD:  {df['pnerd_score'].min():.2f} ({df.iloc[-1]['name']})")
        print(f"  Average pNERD: {df['pnerd_score'].mean():.2f}")
        print(f"  Median pNERD:  {df['pnerd_score'].median():.2f}")
        print()

        # Show top 10 pitchers
        print("Top 10 pitchers by pNERD score:")
        top_10 = df[["name", "team", "pnerd_score"]].head(10)
        for i, row in top_10.iterrows():
            print(f"  {row['name']} ({row['team']}): {row['pnerd_score']:.2f}")
        print()

        # Create analysis directory if it doesn't exist
        analysis_dir = Path("analysis")
        analysis_dir.mkdir(exist_ok=True)

        # Export to CSV
        csv_filename = analysis_dir / "pitcher_pnerd_analysis.csv"

        df.to_csv(csv_filename, index=False)
        print(f"✓ CSV exported successfully: {csv_filename}")
        print(f"  Exported {len(df)} pitchers")
        print(f"  Exported {len(df.columns)} columns")

        # Show column summary organized by category
        print("\nExported columns:")
        
        basic_cols = ["name", "team", "pnerd_score"]
        raw_cols = [col for col in df.columns if col.startswith("raw_")]
        z_cols = [col for col in df.columns if col.startswith("z_")]
        adj_cols = [col for col in df.columns if col.startswith("adjusted_")]
        comp_cols = [col for col in df.columns if col.startswith("component_")]
        
        print("  Basic info:")
        for col in basic_cols:
            print(f"    {col}")
        print("  Raw statistics:")
        for col in raw_cols:
            print(f"    {col}")
        print("  Z-scores:")
        for col in z_cols:
            print(f"    {col}")
        print("  Adjusted values:")
        for col in adj_cols:
            print(f"    {col}")
        print("  pNERD components:")
        for col in comp_cols:
            print(f"    {col}")

        # Verify component totals add up correctly
        print("\nVerifying pNERD calculations...")
        component_sum = (
            df["component_xfip"] +
            df["component_swinging_strike"] +
            df["component_strike_rate"] +
            df["component_velocity"] +
            df["component_age"] +
            df["component_pace"] +
            df["component_luck"] +
            df["component_knuckleball"] +
            df["component_constant"]
        )
        
        max_diff = abs(df["pnerd_score"] - component_sum).max()
        if max_diff < 0.001:
            print("✓ All pNERD calculations verified (components sum to total)")
        else:
            print(f"⚠️ Max calculation difference: {max_diff:.6f}")

        return df

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main() -> None:
    """Main function to handle command line arguments."""
    season = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    
    try:
        generate_comprehensive_pnerd_analysis(season)
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()