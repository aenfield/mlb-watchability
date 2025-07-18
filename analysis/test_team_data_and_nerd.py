#!/usr/bin/env python3
"""
Test script to calculate tNERD for each team using pybaseball library and payroll CSV data.
"""

from typing import Any

import numpy as np
import pandas as pd
import pybaseball as pb
from scipy import stats  # type: ignore


def load_payroll_data() -> pd.DataFrame:
    """Load payroll data from CSV file."""
    return pd.read_csv("data/payroll-spotrac.2025.csv")


def get_team_batting_stats() -> Any:
    """Retrieve team batting statistics from pybaseball."""
    # Get current season team batting stats
    return pb.team_batting(2025)


def calculate_z_scores(data: pd.DataFrame, column: str) -> Any:
    """Calculate z-scores for a given column."""
    return stats.zscore(data[column], nan_policy="omit")


def calculate_tnerd(
    batting_stats: pd.DataFrame, payroll_data: pd.DataFrame
) -> pd.DataFrame | None:
    """Calculate tNERD for each team."""
    # Create reverse team abbreviation mapping (payroll -> batting_stats names)
    payroll_to_batting_mapping = {
        "TB": "TBR",
        "WSH": "WSN",
        "SD": "SDP",
        "SF": "SFG",
        "KC": "KCR",
    }

    # Apply team name mapping to payroll data to match batting stats
    payroll_data["Team"] = payroll_data["Team"].replace(payroll_to_batting_mapping)

    # First, let's see what team abbreviations we have
    print("Team abbreviations in batting stats:", batting_stats["Team"].unique())
    print("Team abbreviations in payroll data:", payroll_data["Team"].unique())

    # Rename Age column in payroll data to avoid conflict
    payroll_data_renamed = payroll_data.rename(columns={"Age": "Payroll_Age"})

    # Merge on team abbreviation
    merged_data = pd.merge(batting_stats, payroll_data_renamed, on="Team", how="inner")

    # Check if we have all required columns
    required_columns = ["Bat", "Barrel%", "BsR", "Fld", "wRC", "R"]
    missing_columns = [
        col for col in required_columns if col not in merged_data.columns
    ]

    if missing_columns:
        print(f"Missing columns: {missing_columns}")
        print("Available columns:", merged_data.columns.tolist())
        return None

    # Calculate Luck as wRC minus Runs
    merged_data["Luck"] = merged_data["wRC"] - merged_data["R"]

    # Calculate z-scores for each component
    merged_data["z_Bat"] = calculate_z_scores(merged_data, "Bat")
    merged_data["z_Barrel"] = calculate_z_scores(merged_data, "Barrel%")
    merged_data["z_BsR"] = calculate_z_scores(merged_data, "BsR")
    merged_data["z_Fld"] = calculate_z_scores(merged_data, "Fld")
    merged_data["z_Luck"] = calculate_z_scores(merged_data, "Luck")

    # For payroll, lower is better, so we need to invert the z-score
    merged_data["z_Pay"] = -calculate_z_scores(merged_data, "Payroll")

    # For age, younger is better, so we need to invert the z-score
    merged_data["z_Age"] = -calculate_z_scores(merged_data, "Payroll_Age")

    # Teams are never assessed negative scores for Pay, Age, and Luck, so set negative values to zero
    merged_data["z_Pay"] = np.maximum(merged_data["z_Pay"], 0)
    merged_data["z_Age"] = np.maximum(merged_data["z_Age"], 0)
    merged_data["z_Luck"] = np.maximum(merged_data["z_Luck"], 0)

    # Cap Luck at 2.0
    merged_data["z_Luck"] = np.minimum(merged_data["z_Luck"], 2.0)

    # Calculate tNERD: zBat + zBarrel% + zBsR + zFld + zPay + zAge + zLuck + Constant
    constant = 4.0
    merged_data["tNERD"] = (
        merged_data["z_Bat"]
        + merged_data["z_Barrel"]
        + merged_data["z_BsR"]
        + merged_data["z_Fld"]
        + merged_data["z_Pay"]
        + merged_data["z_Age"]
        + merged_data["z_Luck"]
        + constant
    )

    return merged_data


def main() -> None:
    """Main function to calculate and display tNERD scores."""
    print("Loading payroll data...")
    payroll_data = load_payroll_data()

    print("Retrieving team batting statistics...")
    try:
        batting_stats = get_team_batting_stats()
    except Exception as e:
        print(f"Error retrieving batting stats: {e}")
        return

    print("Calculating tNERD scores...")
    results = calculate_tnerd(batting_stats, payroll_data)

    if results is None:
        print("Could not calculate tNERD scores due to missing data.")
        return

    # Display results sorted by tNERD score (highest first)
    display_columns = [
        "Team",
        "Bat",
        "z_Bat",
        "Barrel%",
        "z_Barrel",
        "BsR",
        "z_BsR",
        "Fld",
        "z_Fld",
        "Payroll",
        "z_Pay",
        "Age",
        "Payroll_Age",
        "z_Age",
        "wRC",
        "R",
        "Luck",
        "z_Luck",
        "tNERD",
    ]
    results_sorted = results[display_columns].sort_values("tNERD", ascending=False)

    print("\ntNERD Scores by Team (highest to lowest):")
    print("=" * 80)
    print(results_sorted.to_string(index=False, float_format="%.3f"))

    print(f"\nAverage tNERD: {results['tNERD'].mean():.3f}")
    print(f"Standard deviation: {results['tNERD'].std():.3f}")
    print(f"Range: {results['tNERD'].min():.3f} to {results['tNERD'].max():.3f}")

    # Save results to CSV file
    csv_filename = "team-tnerd.csv"
    results_sorted.to_csv(csv_filename, index=False)
    print(f"\nResults saved to {csv_filename}")


if __name__ == "__main__":
    main()
