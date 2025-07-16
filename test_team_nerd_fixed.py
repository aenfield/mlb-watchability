# ruff: skip-file

# skip linting and typing checks since this is a quickie script for understanding the data and API
# type: ignore
"""Fixed team NERD score calculation test script."""


import numpy as np
import pandas as pd
import pybaseball as pb


def get_sample_team_data() -> pd.DataFrame:
    """Get team data and create sample tNERD calculations."""

    print("Retrieving team data from pybaseball...")
    print("=" * 60)

    # Get team data
    team_batting = pb.team_batting(2024)
    team_pitching = pb.team_pitching(2024)
    team_fielding = pb.team_fielding(2024)

    print(f"Retrieved {len(team_batting)} teams from batting data")
    print(f"Retrieved {len(team_pitching)} teams from pitching data")
    print(f"Retrieved {len(team_fielding)} teams from fielding data")

    # Merge the data
    team_data = team_batting[
        ["Team", "HR", "AB", "PA", "Age", "Off", "BsR", "Def", "WAR"]
    ].copy()

    # Add pitching data (for bullpen xFIP calculation)
    pitching_subset = team_pitching[
        ["Team", "xFIP", "Relief-IP", "Starting", "W", "L"]
    ].copy()
    team_data = team_data.merge(pitching_subset, on="Team", how="left")

    print(f"\nMerged data shape: {team_data.shape}")
    print(f"Columns: {list(team_data.columns)}")

    return team_data


def calculate_tnerd_components(team_data: pd.DataFrame) -> pd.DataFrame:
    """Calculate tNERD components from available data."""

    print("\nCalculating tNERD components...")
    print("=" * 60)

    tnerd_data = team_data.copy()

    # 1. Batting Runs (Bat) - Use 'Off' column which is offensive runs above average
    tnerd_data["batting_runs"] = tnerd_data["Off"]
    print("✓ Batting Runs: Using 'Off' column (offensive runs above average)")

    # 2. Home Run Rate (HR%) - Calculate HR/AB
    tnerd_data["home_run_rate"] = tnerd_data["HR"] / tnerd_data["AB"]
    print("✓ HR Rate: Calculated as HR/AB")

    # 3. Baserunning Runs (BsR) - Use 'BsR' column directly
    tnerd_data["baserunning_runs"] = tnerd_data["BsR"]
    print("✓ Baserunning Runs: Using 'BsR' column directly")

    # 4. Bullpen xFIP (Bull) - Use team xFIP as approximation
    # Note: This is not ideal since it includes starters, but it's what we have
    tnerd_data["bullpen_xfip"] = tnerd_data["xFIP"]
    print("~ Bullpen xFIP: Using team xFIP (includes starters - not ideal)")

    # 5. Defensive Runs (Def) - Use 'Def' column from batting data
    tnerd_data["defensive_runs"] = tnerd_data["Def"]
    print("✓ Defensive Runs: Using 'Def' column from batting data")

    # 6. Payroll (Pay) - Use realistic variation instead of placeholder
    # Create some realistic payroll variation based on team performance
    np.random.seed(42)  # For reproducible results
    base_payroll = 140.0
    payroll_variation = 50.0
    tnerd_data["payroll"] = (
        base_payroll + (np.random.random(len(tnerd_data)) - 0.5) * 2 * payroll_variation
    )
    print("~ Payroll: Using simulated variation ($90M-$190M range)")

    # 7. Age - Use 'Age' column from batting data
    tnerd_data["age"] = tnerd_data["Age"]
    print("✓ Age: Using 'Age' column from batting data")

    # 8. Luck - Calculate expected wins from WAR vs actual wins
    # Improved approximation: Expected wins ≈ 81 + (team WAR * 3)
    # More conservative WAR-to-wins conversion
    expected_wins = 81 + (tnerd_data["WAR"] * 3)
    actual_wins = tnerd_data["W"]
    tnerd_data["luck"] = expected_wins - actual_wins
    print("~ Luck: Calculated as (81 + WAR*3) - Actual Wins")

    return tnerd_data


def calculate_z_scores(values: pd.Series) -> pd.Series:
    """Calculate z-scores for a series of values."""
    mean_val = values.mean()
    std_val = values.std()

    # Handle case where std_val is 0 (all values are the same)
    if std_val == 0:
        return pd.Series(0.0, index=values.index)

    return (values - mean_val) / std_val


def calculate_tnerd_scores(tnerd_data: pd.DataFrame) -> pd.DataFrame:
    """Calculate actual tNERD scores using the formula."""

    print("\nCalculating tNERD scores...")
    print("=" * 60)

    result = tnerd_data.copy()

    # Calculate z-scores for each component
    components = [
        "batting_runs",
        "home_run_rate",
        "baserunning_runs",
        "bullpen_xfip",
        "defensive_runs",
        "payroll",
        "age",
    ]

    print("Calculating z-scores for each component:")
    for component in components:
        z_col = f"z_{component}"
        result[z_col] = calculate_z_scores(result[component])

        mean_val = result[component].mean()
        std_val = result[component].std()
        print(f"  {component}: mean={mean_val:.2f}, std={std_val:.2f}")

    # Apply adjustments according to tNERD formula
    print("\nApplying tNERD adjustments:")

    # For payroll, below average is better, so we want negative z_payroll values
    # We flip the sign and then apply positive-only rules
    result["adjusted_payroll"] = np.maximum(0.0, -result["z_payroll"])
    print("  Payroll: Flipped sign (below average is better), positive only")

    # For age, younger is better, so we want negative z_age values (below mean age)
    # We flip the sign and then apply positive-only rules
    result["adjusted_age"] = np.maximum(0.0, -result["z_age"])
    print("  Age: Flipped sign (younger is better), positive only")

    # Luck is capped at 2.0, positive only
    result["adjusted_luck"] = np.maximum(0.0, np.minimum(2.0, result["luck"]))
    print("  Luck: Capped at 2.0, positive only")

    # For bullpen xFIP, lower is better, so we flip the sign
    result["z_bullpen_xfip_flipped"] = -result["z_bullpen_xfip"]
    print("  Bullpen xFIP: Flipped sign (lower is better)")

    # Calculate tNERD score using the formula:
    # zBat + zHR% + zBsR + (zBull / 2) + (zDef / 2) + zPay + zAge + (Luck / 2) + Constant
    constant = 4.0

    result["tnerd_score"] = (
        result["z_batting_runs"]
        + result["z_home_run_rate"]
        + result["z_baserunning_runs"]
        + (result["z_bullpen_xfip_flipped"] / 2)  # Flipped: lower xFIP is better
        + (result["z_defensive_runs"] / 2)
        + result["adjusted_payroll"]
        + result["adjusted_age"]
        + (result["adjusted_luck"] / 2)
        + constant
    )

    print(f"  Applied formula with constant = {constant}")

    return result


def display_sample_results(tnerd_data: pd.DataFrame) -> None:
    """Display sample tNERD calculation results."""

    print("\nSample tNERD Results (Top 10 teams by tNERD score):")
    print("=" * 90)

    # Sort by tNERD score
    sorted_data = tnerd_data.sort_values("tnerd_score", ascending=False)

    # Select columns to display
    display_cols = [
        "Team",
        "tnerd_score",
        "batting_runs",
        "home_run_rate",
        "baserunning_runs",
        "defensive_runs",
        "age",
        "luck",
        "W",
        "L",
    ]

    sample = sorted_data[display_cols].head(10)
    print(sample.to_string(index=False, float_format="%.2f"))

    print("\ntNERD Score Statistics:")
    print(f"  Mean: {tnerd_data['tnerd_score'].mean():.2f}")
    print(f"  Std:  {tnerd_data['tnerd_score'].std():.2f}")
    print(f"  Min:  {tnerd_data['tnerd_score'].min():.2f}")
    print(f"  Max:  {tnerd_data['tnerd_score'].max():.2f}")

    print("\nDetailed breakdown for top 3 teams:")
    print("-" * 60)

    for i, (_idx, team) in enumerate(sorted_data.head(3).iterrows()):
        print(f"\n{i+1}. {team['Team']} - tNERD: {team['tnerd_score']:.2f}")
        print(
            f"   Batting Runs: {team['batting_runs']:.1f} (z: {team['z_batting_runs']:.2f})"
        )
        print(
            f"   HR Rate: {team['home_run_rate']:.3f} (z: {team['z_home_run_rate']:.2f})"
        )
        print(
            f"   Baserunning: {team['baserunning_runs']:.1f} (z: {team['z_baserunning_runs']:.2f})"
        )
        print(
            f"   Bullpen xFIP: {team['bullpen_xfip']:.2f} (z_flipped: {team['z_bullpen_xfip_flipped']:.2f})"
        )
        print(
            f"   Defense: {team['defensive_runs']:.1f} (z: {team['z_defensive_runs']:.2f})"
        )
        print(
            f"   Payroll: ${team['payroll']:.0f}M (adj: {team['adjusted_payroll']:.2f})"
        )
        print(f"   Age: {team['age']:.1f} (adj: {team['adjusted_age']:.2f})")
        print(f"   Luck: {team['luck']:.1f} (adj: {team['adjusted_luck']:.2f})")
        print(f"   Record: {team['W']:.0f}-{team['L']:.0f}")


def test_specific_teams(tnerd_data: pd.DataFrame) -> None:
    """Test specific teams mentioned in requirements."""

    print("\nSpecific Team Analysis:")
    print("=" * 60)

    target_teams = ["LAD", "NYY", "BAL", "HOU", "PHI"]

    for team_code in target_teams:
        team_data = tnerd_data[tnerd_data["Team"] == team_code]

        if len(team_data) > 0:
            team = team_data.iloc[0]
            print(f"\n{team_code} - tNERD: {team['tnerd_score']:.2f}")
            print(
                f"  Components: Bat={team['batting_runs']:.1f}, HR%={team['home_run_rate']:.3f}, "
                f"BsR={team['baserunning_runs']:.1f}, Def={team['defensive_runs']:.1f}"
            )
            print(
                f"  Age={team['age']:.1f}, Payroll=${team['payroll']:.0f}M, Luck={team['luck']:.1f}"
            )
            print(f"  Record: {team['W']:.0f}-{team['L']:.0f}")
        else:
            print(f"\n{team_code}: Not found in data")


def demonstrate_with_sample_teams(tnerd_data: pd.DataFrame) -> None:
    """Create a sample game scenario using calculated tNERD scores."""

    print("\nSample Game Scenario:")
    print("=" * 60)

    # Pick two teams for a sample game
    sorted_teams = tnerd_data.sort_values("tnerd_score", ascending=False)
    team1 = sorted_teams.iloc[0]
    team2 = sorted_teams.iloc[5]  # Pick 6th best team for contrast

    print(f"Hypothetical Game: {team1['Team']} vs {team2['Team']}")
    print("")
    print(f"{team1['Team']} tNERD: {team1['tnerd_score']:.2f}")
    print(f"  Record: {team1['W']:.0f}-{team1['L']:.0f}")
    print(
        f"  Strengths: Batting={team1['batting_runs']:.1f}, Defense={team1['defensive_runs']:.1f}"
    )
    print("")
    print(f"{team2['Team']} tNERD: {team2['tnerd_score']:.2f}")
    print(f"  Record: {team2['W']:.0f}-{team2['L']:.0f}")
    print(
        f"  Strengths: Batting={team2['batting_runs']:.1f}, Defense={team2['defensive_runs']:.1f}"
    )
    print("")

    # Calculate average tNERD for the game (would be combined with pNERD for gNERD)
    avg_tnerd = (team1["tnerd_score"] + team2["tnerd_score"]) / 2
    print(f"Average tNERD for this matchup: {avg_tnerd:.2f}")
    print("(Note: This would be combined with pNERD scores to calculate final gNERD)")


def main():
    """Main execution function."""

    print("Team NERD Score Calculation Test (Fixed)")
    print("=" * 60)
    print("Testing tNERD calculation using available pybaseball data")
    print("Note: This is a preliminary test with some simulated data")

    try:
        # Get team data
        team_data = get_sample_team_data()

        # Calculate tNERD components
        tnerd_data = calculate_tnerd_components(team_data)

        # Calculate tNERD scores
        tnerd_scores = calculate_tnerd_scores(tnerd_data)

        # Display results
        display_sample_results(tnerd_scores)

        # Test specific teams
        test_specific_teams(tnerd_scores)

        # Demonstrate sample game scenario
        demonstrate_with_sample_teams(tnerd_scores)

        print("\n" + "=" * 60)
        print("CONCLUSION")
        print("=" * 60)

        print("Successfully calculated tNERD scores!")
        print("\nKey findings:")
        print("• Most tNERD components can be calculated from pybaseball team data")
        print(
            "• Batting runs, HR%, baserunning, defense, and age are directly available"
        )
        print("• Bullpen xFIP needs refinement (currently uses team xFIP)")
        print("• Payroll requires external data source")
        print("• Expected wins calculation can be improved")

        print("\nNext steps for production implementation:")
        print("1. Calculate proper bullpen xFIP from individual relief pitcher data")
        print("2. Integrate external payroll data source (Spotrac, etc.)")
        print("3. Refine expected wins calculation methodology")
        print("4. Add proper error handling and data validation")
        print("5. Integrate with pitcher NERD scores for complete gNERD calculation")

        # Save results
        output_file = "fixed_tnerd_results.csv"
        tnerd_scores.to_csv(output_file, index=False)
        print(f"\nSaved results to {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        # Import here since this is an error handling path
        import traceback  # noqa: PLC0415

        traceback.print_exc()


if __name__ == "__main__":
    main()
