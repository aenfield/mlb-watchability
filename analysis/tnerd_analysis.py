#!/usr/bin/env python3
"""
Analysis script to examine tNERD scores for all MLB teams.

This script calculates tNERD scores for all MLB teams and provides detailed
statistics to understand the distribution and range of tNERD scores. Since
team stats don't change frequently and the data source doesn't provide
historical data, we analyze the current state of all teams.
"""

import sys
from pathlib import Path

import pandas as pd

# Add the src directory to the Python path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mlb_watchability.team_stats import (
    calculate_detailed_team_nerd_scores,
    get_all_team_stats_objects,
)


def collect_team_data() -> pd.DataFrame:
    """
    Collect all team statistics and calculate tNERD scores.

    Returns a DataFrame with team data and tNERD scores.
    """
    print("Fetching team statistics and calculating tNERD scores...")

    # Get team stats objects
    team_stats_dict = get_all_team_stats_objects(2025)

    # Get detailed tNERD statistics for all teams
    team_nerd_stats = calculate_detailed_team_nerd_scores(2025)

    # Build list of team data
    team_data = []

    for team_abbr, team_stats in team_stats_dict.items():
        nerd_stats = team_nerd_stats.get(team_abbr)

        row = {
            "team_name": team_stats.name,
            "team_abbr": team_abbr,
            "batting_runs": team_stats.batting_runs,
            "barrel_rate": team_stats.barrel_rate,
            "baserunning_runs": team_stats.baserunning_runs,
            "fielding_runs": team_stats.fielding_runs,
            "payroll": team_stats.payroll,
            "age": team_stats.age,
            "luck": team_stats.luck,
        }

        if nerd_stats:
            row.update(
                {
                    "tnerd_score": nerd_stats.tnerd_score,
                    "z_batting_runs": nerd_stats.z_batting_runs,
                    "z_barrel_rate": nerd_stats.z_barrel_rate,
                    "z_baserunning_runs": nerd_stats.z_baserunning_runs,
                    "z_fielding_runs": nerd_stats.z_fielding_runs,
                    "z_payroll": nerd_stats.z_payroll,
                    "z_age": nerd_stats.z_age,
                    "z_luck": nerd_stats.z_luck,
                    "adjusted_payroll": nerd_stats.adjusted_payroll,
                    "adjusted_age": nerd_stats.adjusted_age,
                    "adjusted_luck": nerd_stats.adjusted_luck,
                    "batting_component": nerd_stats.batting_component,
                    "barrel_component": nerd_stats.barrel_component,
                    "baserunning_component": nerd_stats.baserunning_component,
                    "fielding_component": nerd_stats.fielding_component,
                    "payroll_component": nerd_stats.payroll_component,
                    "age_component": nerd_stats.age_component,
                    "luck_component": nerd_stats.luck_component,
                    "constant_component": nerd_stats.constant_component,
                }
            )
        else:
            # Mark as missing data
            for field in [
                "tnerd_score",
                "z_batting_runs",
                "z_barrel_rate",
                "z_baserunning_runs",
                "z_fielding_runs",
                "z_payroll",
                "z_age",
                "z_luck",
                "adjusted_payroll",
                "adjusted_age",
                "adjusted_luck",
                "batting_component",
                "barrel_component",
                "baserunning_component",
                "fielding_component",
                "payroll_component",
                "age_component",
                "luck_component",
                "constant_component",
            ]:
                row[field] = None

        team_data.append(row)

    # Convert to DataFrame and sort by tNERD score descending
    df = pd.DataFrame(team_data)
    df = df.sort_values("tnerd_score", ascending=False, na_position="last")

    return df


def analyze_tnerd_distribution(df: pd.DataFrame) -> None:
    """
    Calculate and display descriptive statistics for tNERD score distribution.
    """
    print("\n" + "=" * 80)
    print("TNERD SCORE DISTRIBUTION ANALYSIS")
    print("=" * 80)

    # Filter out rows with missing tNERD scores
    valid_scores = df.dropna(subset=["tnerd_score"])

    print(f"\nData Summary:")
    print(f"  Total teams: {len(df)}")
    print(f"  Teams with tNERD scores: {len(valid_scores)}")
    print(f"  Missing tNERD scores: {len(df) - len(valid_scores)}")

    if len(valid_scores) == 0:
        print("\nNo valid tNERD scores found!")
        return

    # Basic descriptive statistics
    tnerd_scores = valid_scores["tnerd_score"]

    print(f"\nBasic Statistics:")
    print(f"  Mean: {tnerd_scores.mean():.3f}")
    print(f"  Median: {tnerd_scores.median():.3f}")
    print(f"  Standard Deviation: {tnerd_scores.std():.3f}")
    print(f"  Minimum: {tnerd_scores.min():.3f}")
    print(f"  Maximum: {tnerd_scores.max():.3f}")
    print(f"  Range: {tnerd_scores.max() - tnerd_scores.min():.3f}")

    # Percentiles
    print(f"\nPercentiles:")
    for p in [10, 25, 50, 75, 90, 95]:
        value = tnerd_scores.quantile(p / 100)
        print(f"  {p}th percentile: {value:.3f}")

    # Distribution by bins
    print(f"\nScore Distribution (by ranges):")
    bins = [0, 2, 4, 6, 8, 10, 12, 15]
    for i in range(len(bins) - 1):
        low, high = bins[i], bins[i + 1]
        count = len(tnerd_scores[(tnerd_scores >= low) & (tnerd_scores < high)])
        pct = count / len(tnerd_scores) * 100
        print(f"  {low:.0f} to {high:.0f}: {count} teams ({pct:.1f}%)")

    # Above/below average analysis
    mean = tnerd_scores.mean()
    above_avg = len(tnerd_scores[tnerd_scores > mean])
    below_avg = len(tnerd_scores[tnerd_scores < mean])

    print(f"\nAbove/Below Average:")
    print(f"  Above average (> {mean:.3f}): {above_avg} teams")
    print(f"  Below average (< {mean:.3f}): {below_avg} teams")

    # Top and bottom performers
    print(f"\nTop 5 teams:")
    top_teams = valid_scores.head(5)[["team_name", "tnerd_score"]]
    for _, row in top_teams.iterrows():
        print(f"  {row['team_name']}: {row['tnerd_score']:.3f}")

    print(f"\nBottom 5 teams:")
    bottom_teams = valid_scores.tail(5)[["team_name", "tnerd_score"]]
    for _, row in bottom_teams.iterrows():
        print(f"  {row['team_name']}: {row['tnerd_score']:.3f}")


def analyze_component_contributions(df: pd.DataFrame) -> None:
    """
    Analyze how different components contribute to tNERD scores.
    """
    print("\n" + "=" * 80)
    print("TNERD COMPONENT ANALYSIS")
    print("=" * 80)

    # Filter out rows with missing tNERD scores
    valid_scores = df.dropna(subset=["tnerd_score"])

    if len(valid_scores) == 0:
        print("\nNo valid tNERD scores found!")
        return

    components = [
        "batting_component",
        "barrel_component",
        "baserunning_component",
        "fielding_component",
        "payroll_component",
        "age_component",
        "luck_component",
        "constant_component",
    ]

    print(f"\nComponent Statistics (mean ± std):")
    for component in components:
        if component in valid_scores.columns:
            values = valid_scores[component].dropna()
            if len(values) > 0:
                mean_val = values.mean()
                std_val = values.std()
                print(f"  {component:20}: {mean_val:6.3f} ± {std_val:5.3f}")

    # Correlation with total tNERD score
    print(f"\nCorrelation with total tNERD score:")
    for component in components:
        if component in valid_scores.columns:
            corr = valid_scores["tnerd_score"].corr(valid_scores[component])
            if not pd.isna(corr):
                print(f"  {component:20}: {corr:6.3f}")


def analyze_team_characteristics(df: pd.DataFrame) -> None:
    """
    Analyze team characteristics and their relationship to tNERD scores.
    """
    print("\n" + "=" * 80)
    print("TEAM CHARACTERISTICS ANALYSIS")
    print("=" * 80)

    # Filter out rows with missing tNERD scores
    valid_scores = df.dropna(subset=["tnerd_score"])

    if len(valid_scores) == 0:
        print("\nNo valid tNERD scores found!")
        return

    # Raw stat distributions
    raw_stats = [
        "batting_runs",
        "barrel_rate",
        "baserunning_runs",
        "fielding_runs",
        "payroll",
        "age",
        "luck",
    ]

    print(f"\nRaw Statistics Distribution:")
    for stat in raw_stats:
        if stat in valid_scores.columns:
            values = valid_scores[stat].dropna()
            if len(values) > 0:
                mean_val = values.mean()
                std_val = values.std()
                min_val = values.min()
                max_val = values.max()
                print(
                    f"  {stat:18}: {mean_val:7.2f} ± {std_val:6.2f} (range: {min_val:6.2f} to {max_val:6.2f})"
                )

    # Correlation between raw stats and tNERD
    print(f"\nCorrelation between raw stats and tNERD:")
    for stat in raw_stats:
        if stat in valid_scores.columns:
            corr = valid_scores["tnerd_score"].corr(valid_scores[stat])
            if not pd.isna(corr):
                print(f"  {stat:18}: {corr:6.3f}")


def main() -> None:
    """Main analysis function."""
    print("MLB tNERD Score Analysis - All Teams")
    print("=" * 50)

    # Collect team data and calculate tNERD scores
    print("\nCollecting team data and calculating tNERD scores...")
    df = collect_team_data()

    if df.empty:
        print("No team data found!")
        return

    print(f"Found {len(df)} teams")

    # Save raw data to CSV
    output_file = "analysis/tnerd_analysis_raw_data.csv"
    df.to_csv(output_file, index=False)
    print(f"\nRaw data saved to: {output_file}")

    # Perform analysis
    analyze_tnerd_distribution(df)
    analyze_component_contributions(df)
    analyze_team_characteristics(df)

    print(f"\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
