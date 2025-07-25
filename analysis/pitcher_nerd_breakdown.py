#!/usr/bin/env python3
"""
Pitcher NERD Score Breakdown Analysis Script

Calculates and displays the detailed pNERD score breakdown for a specified pitcher.
Shows raw stats, z-scores, adjusted values, and formula components.
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mlb_watchability.pitcher_stats import (
    calculate_detailed_pitcher_nerd_scores,
    find_pitcher_nerd_stats_fuzzy,
)


def analyze_pitcher_nerd(pitcher_name: str, season: int = 2025) -> None:
    """
    Analyze and display detailed pNERD breakdown for a pitcher.

    Args:
        pitcher_name: Name of the pitcher to analyze
        season: Season year (default: 2025)
    """
    print("Pitcher NERD Score Breakdown Analysis")
    print("=" * 50)
    print(f"Pitcher: {pitcher_name}")
    print(f"Season: {season}")
    print()

    # Get all pitcher NERD stats
    try:
        pitcher_nerd_details = calculate_detailed_pitcher_nerd_scores(season)
    except Exception as e:
        print(f"Error calculating pitcher NERD scores: {e}")
        return

    # Find the specified pitcher using fuzzy matching
    pitcher_stats = find_pitcher_nerd_stats_fuzzy(pitcher_nerd_details, pitcher_name)

    if pitcher_stats is None:
        print(f"❌ Pitcher '{pitcher_name}' not found.")
        print("\nAvailable pitchers:")
        for name in sorted(pitcher_nerd_details.keys()):
            print(f"  - {name}")
        return

    # Extract data for easier access
    raw_stats = pitcher_stats.pitcher_stats
    nerd_stats = pitcher_stats

    print(f"✅ Found pitcher: {raw_stats.name}")
    if raw_stats.name != pitcher_name:
        print(f"   (searched for: {pitcher_name})")
    print(f"Team: {raw_stats.team}")
    print()

    # Raw Statistics
    print("RAW STATISTICS")
    print("-" * 30)
    print(f"xFIP-:              {raw_stats.xfip_minus:>8.1f}")
    print(f"Swinging Strike %:  {raw_stats.swinging_strike_rate:>8.3f}")
    print(f"Strike %:           {raw_stats.strike_rate:>8.3f}")
    print(f"Velocity (mph):     {raw_stats.velocity:>8.1f}")
    print(f"Age (years):        {raw_stats.age:>8d}")
    print(f"Pace (seconds):     {raw_stats.pace:>8.1f}")
    print(f"Luck (ERA- - xFIP-): {raw_stats.luck:>7.1f}")
    print(f"Knuckleball %:      {raw_stats.knuckleball_rate:>8.3f}")
    print()

    # Z-Scores
    print("Z-SCORES (Standard Deviations from League Mean)")
    print("-" * 50)
    print(f"z xFIP-:            {nerd_stats.z_xfip_minus:>8.2f}  (lower is better)")
    print(
        f"z Swinging Strike:  {nerd_stats.z_swinging_strike_rate:>8.2f}  (higher is better)"
    )
    print(f"z Strike Rate:      {nerd_stats.z_strike_rate:>8.2f}  (higher is better)")
    print(f"z Velocity:         {nerd_stats.z_velocity:>8.2f}  (higher is better)")
    print(f"z Age:              {nerd_stats.z_age:>8.2f}  (lower is better)")
    print(f"z Pace:             {nerd_stats.z_pace:>8.2f}  (lower is better)")
    print()

    # Adjusted Values
    print("ADJUSTED VALUES (After Caps and Rules)")
    print("-" * 40)
    print(
        f"Adjusted Velocity:  {nerd_stats.adjusted_velocity:>8.2f}  (capped at 2.0, positive only)"
    )
    print(
        f"Adjusted Age:       {nerd_stats.adjusted_age:>8.2f}  (capped at 2.0, positive only)"
    )
    print(
        f"Adjusted Luck:      {nerd_stats.adjusted_luck:>8.2f}  (capped at 1.0, positive only)"
    )
    print()

    # pNERD Formula Breakdown
    print("pNERD FORMULA BREAKDOWN")
    print("-" * 30)

    # Use the individual component fields directly
    print(f"(-z xFIP- × 2):     {nerd_stats.xfip_component:>8.2f}")
    print(f"(z SwStr ÷ 2):      {nerd_stats.swinging_strike_component:>8.2f}")
    print(f"(z Strike ÷ 2):     {nerd_stats.strike_component:>8.2f}")
    print(f"Adjusted Velocity:  {nerd_stats.velocity_component:>8.2f}")
    print(f"Adjusted Age:       {nerd_stats.age_component:>8.2f}")
    print(f"(-z Pace ÷ 2):      {nerd_stats.pace_component:>8.2f}")
    print(f"(Luck ÷ 20):        {nerd_stats.luck_component:>8.2f}")
    print(f"(KN% × 5):          {nerd_stats.knuckleball_component:>8.2f}")
    print(f"Constant:           {nerd_stats.constant_component:>8.1f}")
    print(f"{'-' * 20}")

    # Calculate total using individual component fields
    calculated_total = (
        nerd_stats.xfip_component
        + nerd_stats.swinging_strike_component
        + nerd_stats.strike_component
        + nerd_stats.velocity_component
        + nerd_stats.age_component
        + nerd_stats.pace_component
        + nerd_stats.luck_component
        + nerd_stats.knuckleball_component
        + nerd_stats.constant_component
    )

    print(f"TOTAL pNERD:        {calculated_total:>8.2f}")
    print(f"Stored pNERD:       {nerd_stats.pnerd_score:>8.2f}")

    # Verify calculation matches
    if abs(calculated_total - nerd_stats.pnerd_score) < 0.001:
        print("✅ Calculation verified!")
    else:
        print("⚠️  Calculation mismatch - possible rounding difference")

    print()
    print("FORMULA:")
    print("pNERD = (-z xFIP- × 2) + (z SwStr ÷ 2) + (z Strike ÷ 2) + Adj Velocity")
    print("        + Adj Age + (-z Pace ÷ 2) + (Luck ÷ 20) + (KN% × 5) + 3.8")


def main() -> None:
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python pitcher_nerd_breakdown.py <pitcher_name> [season]")
        print("Example: python pitcher_nerd_breakdown.py 'Jacob deGrom'")
        print("Example: python pitcher_nerd_breakdown.py 'Jake Latz' 2025")
        sys.exit(1)

    pitcher_name = sys.argv[1]
    season = int(sys.argv[2]) if len(sys.argv) > 2 else 2025

    try:
        analyze_pitcher_nerd(pitcher_name, season)
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
