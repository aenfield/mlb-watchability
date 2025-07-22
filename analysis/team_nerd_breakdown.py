#!/usr/bin/env python3
"""
Team NERD Score Breakdown Analysis Script

Calculates and displays the detailed tNERD score breakdown for a specified team.
Shows raw stats, z-scores, adjusted values, and formula components.
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mlb_watchability.team_stats import calculate_detailed_team_nerd_scores


def analyze_team_nerd(team_name: str, season: int = 2025) -> None:
    """
    Analyze and display detailed tNERD breakdown for a team.

    Args:
        team_name: Name or abbreviation of the team to analyze
        season: Season year (default: 2025)
    """
    print("Team NERD Score Breakdown Analysis")
    print("=" * 50)
    print(f"Team: {team_name}")
    print(f"Season: {season}")
    print()

    # Get all team NERD stats
    try:
        team_nerd_details = calculate_detailed_team_nerd_scores(season)
    except Exception as e:
        print(f"Error calculating team NERD scores: {e}")
        return

    # Find the specified team (try exact match first, then partial match)
    team_stats = None
    matched_team = None

    # Try exact match (case-insensitive)
    for team_abbrev, stats in team_nerd_details.items():
        if (
            team_abbrev.lower() == team_name.lower()
            or stats.team_stats.name.lower() == team_name.lower()
        ):
            team_stats = stats
            matched_team = team_abbrev
            break

    # Try partial match if no exact match
    if team_stats is None:
        for team_abbrev, stats in team_nerd_details.items():
            if (
                team_name.lower() in team_abbrev.lower()
                or team_name.lower() in stats.team_stats.name.lower()
            ):
                team_stats = stats
                matched_team = team_abbrev
                break

    if team_stats is None:
        print(f"❌ Team '{team_name}' not found.")
        print("\nAvailable teams:")
        for abbrev, stats in sorted(team_nerd_details.items()):
            print(f"  - {abbrev}: {stats.team_stats.name}")
        return

    # Extract data for easier access
    raw_stats = team_stats.team_stats
    nerd_stats = team_stats

    print(f"✅ Found team: {raw_stats.name} ({matched_team})")
    if (
        raw_stats.name.lower() != team_name.lower()
        and matched_team is not None
        and matched_team.lower() != team_name.lower()
    ):
        print(f"   (searched for: {team_name})")
    print()

    # Raw Statistics
    print("RAW STATISTICS")
    print("-" * 30)
    print(f"Batting Runs:       {raw_stats.batting_runs:>8.1f}")
    print(f"Barrel Rate %:      {raw_stats.barrel_rate:>8.1f}")
    print(f"Baserunning Runs:   {raw_stats.baserunning_runs:>8.1f}")
    print(f"Fielding Runs:      {raw_stats.fielding_runs:>8.1f}")
    print(f"Payroll ($M):       ${raw_stats.payroll:>7.1f}")
    print(f"Age (years):        {raw_stats.age:>8.1f}")
    print(f"Luck:               {raw_stats.luck:>8.1f}")
    print()

    # Z-Scores
    print("Z-SCORES (Standard Deviations from League Mean)")
    print("-" * 50)
    print(f"z Batting Runs:     {nerd_stats.z_batting_runs:>8.2f}  (higher is better)")
    print(f"z Barrel Rate:      {nerd_stats.z_barrel_rate:>8.2f}  (higher is better)")
    print(
        f"z Baserunning Runs: {nerd_stats.z_baserunning_runs:>8.2f}  (higher is better)"
    )
    print(f"z Fielding Runs:    {nerd_stats.z_fielding_runs:>8.2f}  (higher is better)")
    print(f"z Payroll:          {nerd_stats.z_payroll:>8.2f}  (lower is better)")
    print(f"z Age:              {nerd_stats.z_age:>8.2f}  (lower is better)")
    print(f"z Luck:             {nerd_stats.z_luck:>8.2f}  (higher is better)")
    print()

    # Adjusted Values
    print("ADJUSTED VALUES (After Caps and Rules)")
    print("-" * 40)
    print(
        f"Adjusted Payroll:   {nerd_stats.adjusted_payroll:>8.2f}  (flipped z-score, positive only)"
    )
    print(
        f"Adjusted Age:       {nerd_stats.adjusted_age:>8.2f}  (flipped z-score, positive only)"
    )
    print(
        f"Adjusted Luck:      {nerd_stats.adjusted_luck:>8.2f}  (capped at 2.0, positive only)"
    )
    print()

    # tNERD Formula Breakdown
    print("tNERD FORMULA BREAKDOWN")
    print("-" * 30)

    # Calculate each component (based on actual formula: zBat + zBarrel% + zBsR + zFld + zPay + zAge + zLuck + Constant)
    batting_component = nerd_stats.z_batting_runs
    barrel_component = nerd_stats.z_barrel_rate
    baserunning_component = nerd_stats.z_baserunning_runs
    fielding_component = nerd_stats.z_fielding_runs
    payroll_component = nerd_stats.adjusted_payroll
    age_component = nerd_stats.adjusted_age
    luck_component = nerd_stats.adjusted_luck
    constant = 4.0

    print(f"z Batting Runs:     {batting_component:>8.2f}")
    print(f"z Barrel Rate:      {barrel_component:>8.2f}")
    print(f"z Baserunning Runs: {baserunning_component:>8.2f}")
    print(f"z Fielding Runs:    {fielding_component:>8.2f}")
    print(f"Adjusted Payroll:   {payroll_component:>8.2f}")
    print(f"Adjusted Age:       {age_component:>8.2f}")
    print(f"Adjusted Luck:      {luck_component:>8.2f}")
    print(f"Constant:           {constant:>8.1f}")
    print(f"{'-' * 20}")

    # Calculate total
    calculated_total = (
        batting_component
        + barrel_component
        + baserunning_component
        + fielding_component
        + payroll_component
        + age_component
        + luck_component
        + constant
    )

    print(f"TOTAL tNERD:        {calculated_total:>8.2f}")
    print(f"Stored tNERD:       {nerd_stats.tnerd_score:>8.2f}")

    # Verify calculation matches
    if abs(calculated_total - nerd_stats.tnerd_score) < 0.001:
        print("✅ Calculation verified!")
    else:
        print("⚠️  Calculation mismatch - possible rounding difference")

    print()
    print("FORMULA:")
    print("tNERD = zBat + zBarrel% + zBsR + zFld + AdjPayroll + AdjAge + AdjLuck + 4.0")


def main() -> None:
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python team_nerd_breakdown.py <team_name_or_abbrev> [season]")
        print("Example: python team_nerd_breakdown.py 'Yankees'")
        print("Example: python team_nerd_breakdown.py 'NYY' 2025")
        print("Example: python team_nerd_breakdown.py 'Los Angeles Dodgers'")
        sys.exit(1)

    team_name = sys.argv[1]
    season = int(sys.argv[2]) if len(sys.argv) > 2 else 2025

    try:
        analyze_team_nerd(team_name, season)
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
