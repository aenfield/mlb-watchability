# ruff: skip-file

# skip linting and typing checks since this is a quickie script for understanding the data and API
# type: ignore
"""Detailed test script to explore team statistics data mapping for tNERD calculation."""

import pandas as pd
import pybaseball as pb


def test_detailed_team_stats():
    """Test detailed mapping of team statistics for tNERD calculation."""

    print("Detailed Team Statistics Analysis for tNERD Calculation")
    print("=" * 70)

    try:
        # Try different team statistics functions available in pybaseball
        print("Exploring available team statistics functions in pybaseball...")
        print("-" * 60)

        # Team batting stats
        print("1. Team Batting Stats (pb.team_batting):")
        try:
            team_batting = pb.team_batting(2024)
            print(f"   Retrieved {len(team_batting)} team batting records")
            print(f"   Columns: {list(team_batting.columns)}")
            print()
        except Exception as e:
            print(f"   Error: {e}")
            team_batting = None

        # Team pitching stats
        print("2. Team Pitching Stats (pb.team_pitching):")
        try:
            team_pitching = pb.team_pitching(2024)
            print(f"   Retrieved {len(team_pitching)} team pitching records")
            print(f"   Columns: {list(team_pitching.columns)}")
            print()
        except Exception as e:
            print(f"   Error: {e}")
            team_pitching = None

        # Team fielding stats
        print("3. Team Fielding Stats (pb.team_fielding):")
        try:
            team_fielding = pb.team_fielding(2024)
            print(f"   Retrieved {len(team_fielding)} team fielding records")
            print(f"   Columns: {list(team_fielding.columns)}")
            print()
        except Exception as e:
            print(f"   Error: {e}")
            team_fielding = None

        # Try to get more specific team stats functions
        print("4. Exploring other potential team data sources:")
        try:
            # Check if there are team run expectancy or baserunning stats
            print("   Looking for additional team statistics functions...")

            # List some functions we might try
            potential_functions = [
                "team_results",
                "standings",
                "schedule_and_record",
                "team_stats",
                "league_batting_stats",
                "league_pitching_stats",
            ]

            for func_name in potential_functions:
                if hasattr(pb, func_name):
                    print(f"   ✓ Found function: pb.{func_name}")
                else:
                    print(f"   ✗ Function not found: pb.{func_name}")
            print()
        except Exception as e:
            print(f"   Error exploring functions: {e}")

        print("\n" + "=" * 70)

        # Define what we need for tNERD calculation based on vision-and-reqs.md
        tnerd_requirements = {
            "Bat": {
                "description": "Park-Adjusted Batting Runs Above Average",
                "potential_sources": ["wRC+", "wOBA", "Off", "Offense", "batting runs"],
                "calculation": "Team offensive value above/below average",
            },
            "HR%": {
                "description": "Park-Adjusted Home Run Rate",
                "potential_sources": ["HR%", "HR/FB", "HR"],
                "calculation": "Home runs per at-bat or plate appearance (park-adjusted)",
            },
            "BsR": {
                "description": "Baserunning Runs",
                "potential_sources": ["BsR", "BSR", "baserunning", "SB", "CS"],
                "calculation": "Baserunning value above/below average",
            },
            "Bull": {
                "description": "Bullpen xFIP",
                "potential_sources": ["bullpen xFIP", "Relief xFIP", "xFIP"],
                "calculation": "Expected Fielding Independent Pitching for bullpen",
            },
            "Def": {
                "description": "Defensive Runs",
                "potential_sources": ["Def", "Defense", "UZR", "DRS", "fielding runs"],
                "calculation": "Defensive value above/below average",
            },
            "Pay": {
                "description": "Payroll, Where Below Average Is Better",
                "potential_sources": ["payroll", "salary"],
                "calculation": "External data source (not in pybaseball)",
            },
            "Age": {
                "description": "Batter Age, Where Younger Is Better",
                "potential_sources": ["Age", "average age"],
                "calculation": "Average age of position players",
            },
            "Luck": {
                "description": "Expected Wins, Per WAR, Minus Actual Wins",
                "potential_sources": ["W", "L", "WAR", "wins", "expected wins"],
                "calculation": "Expected wins (from WAR) minus actual wins",
            },
        }

        print("tNERD Statistics Requirements Analysis:")
        print("-" * 50)

        for stat, info in tnerd_requirements.items():
            print(f"\n{stat} ({info['description']}):")
            print(f"  Potential sources: {info['potential_sources']}")
            print(f"  Calculation: {info['calculation']}")

            # Check if we can find relevant columns in our data
            found_columns = []

            if team_batting is not None:
                for source in info["potential_sources"]:
                    matching_cols = [
                        col
                        for col in team_batting.columns
                        if source.lower() in col.lower()
                    ]
                    if matching_cols:
                        found_columns.extend(
                            [(col, "batting") for col in matching_cols]
                        )

            if team_pitching is not None:
                for source in info["potential_sources"]:
                    matching_cols = [
                        col
                        for col in team_pitching.columns
                        if source.lower() in col.lower()
                    ]
                    if matching_cols:
                        found_columns.extend(
                            [(col, "pitching") for col in matching_cols]
                        )

            if team_fielding is not None:
                for source in info["potential_sources"]:
                    matching_cols = [
                        col
                        for col in team_fielding.columns
                        if source.lower() in col.lower()
                    ]
                    if matching_cols:
                        found_columns.extend(
                            [(col, "fielding") for col in matching_cols]
                        )

            if found_columns:
                print("  ✓ Potential matches found:")
                for col, source in found_columns:
                    print(f"    - {col} (from {source})")
            else:
                print("  ✗ No obvious matches found in available data")

        print("\n" + "=" * 70)

        # Detailed analysis of available team data
        if team_batting is not None:
            print("DETAILED TEAM BATTING ANALYSIS")
            print("=" * 70)

            print(f"Team batting data shape: {team_batting.shape}")
            print(f"Teams: {len(team_batting)}")
            print()

            # doesn't work well UI-wise with a normal terminal width
            # print("Sample team batting data (first 5 teams):")
            # print(team_batting.head().to_string())
            # print()

            print("Key columns for tNERD calculation:")
            key_batting_cols = [
                "Team",
                "G",
                "PA",
                "HR",
                "R",
                "RBI",
                "wRC+",
                "wOBA",
                "Off",
            ]
            available_key_cols = [
                col for col in key_batting_cols if col in team_batting.columns
            ]

            if available_key_cols:
                print("Available key columns:")
                sample_data = team_batting[available_key_cols].head(10)
                print(sample_data.to_string())
                print()

            # Look for specific tNERD components
            print("Searching for specific tNERD components in batting data:")

            # Batting runs (Off, wRC+, etc.)
            batting_runs_cols = [
                col
                for col in team_batting.columns
                if any(term in col.lower() for term in ["off", "wrc", "runs", "bat"])
            ]
            if batting_runs_cols:
                print(f"  Batting runs candidates: {batting_runs_cols}")
                sample = team_batting[["Team"] + batting_runs_cols].head(5)
                print(sample.to_string())
                print()

            # Home run rate
            hr_cols = [
                col
                for col in team_batting.columns
                if any(term in col.lower() for term in ["hr%", "hr/", "hr"])
            ]
            if hr_cols:
                print(f"  Home run rate candidates: {hr_cols}")
                sample = team_batting[["Team"] + hr_cols].head(5)
                print(sample.to_string())
                print()

            # Baserunning
            baserunning_cols = [
                col
                for col in team_batting.columns
                if any(term in col.lower() for term in ["bsr", "base", "sb", "cs"])
            ]
            if baserunning_cols:
                print(f"  Baserunning candidates: {baserunning_cols}")
                sample = team_batting[["Team"] + baserunning_cols].head(5)
                print(sample.to_string())
                print()

        if team_pitching is not None:
            print("\n" + "=" * 70)
            print("DETAILED TEAM PITCHING ANALYSIS")
            print("=" * 70)

            print(f"Team pitching data shape: {team_pitching.shape}")
            print(f"Teams: {len(team_pitching)}")
            print()

            # doesn't work well UI-wise with a normal terminal width
            # print("Sample team pitching data (first 5 teams):")
            # print(team_pitching.head().to_string())
            # print()

            # Look for bullpen-specific stats
            print("Searching for bullpen/relief pitching stats:")
            bullpen_cols = [
                col
                for col in team_pitching.columns
                if any(term in col.lower() for term in ["xfip", "relief", "bull", "rp"])
            ]
            if bullpen_cols:
                print(f"  Bullpen candidates: {bullpen_cols}")
                sample = team_pitching[["Team"] + bullpen_cols].head(5)
                print(sample.to_string())
                print()
            else:
                print("  No obvious bullpen-specific columns found")
                print("  May need to calculate from individual pitcher data")
                print()

        if team_fielding is not None:
            print("\n" + "=" * 70)
            print("DETAILED TEAM FIELDING ANALYSIS")
            print("=" * 70)

            print(f"Team fielding data shape: {team_fielding.shape}")
            print(f"Teams: {len(team_fielding)}")
            print()

            print("Sample team fielding data (first 5 teams):")
            print(team_fielding.head().to_string())
            print()

            # Look for defensive metrics
            print("Searching for defensive metrics:")
            def_cols = [
                col
                for col in team_fielding.columns
                if any(
                    term in col.lower() for term in ["def", "uzr", "drs", "fielding"]
                )
            ]
            if def_cols:
                print(f"  Defensive candidates: {def_cols}")
                sample = team_fielding[["Team"] + def_cols].head(5)
                print(sample.to_string())
                print()
            else:
                print("  No obvious defensive run columns found")
                print()

        print("\n" + "=" * 70)

        # Test specific calculations we can make
        print("TESTABLE tNERD CALCULATIONS")
        print("=" * 70)

        if team_batting is not None:
            print("1. Testing HR% calculation:")
            if "HR" in team_batting.columns and "AB" in team_batting.columns:
                sample = team_batting[["Team", "HR", "AB"]].head(5).copy()
                sample["HR%"] = sample["HR"] / sample["AB"]
                print("HR% = HR / AB")
                print(sample.to_string())
                print()
            elif "HR" in team_batting.columns and "PA" in team_batting.columns:
                sample = team_batting[["Team", "HR", "PA"]].head(5).copy()
                sample["HR%"] = sample["HR"] / sample["PA"]
                print("HR% = HR / PA (alternative)")
                print(sample.to_string())
                print()
            else:
                print("Cannot calculate HR% - missing HR, AB, or PA columns")
                print()

            print("2. Testing batting runs approximation:")
            if "wRC+" in team_batting.columns and "PA" in team_batting.columns:
                # wRC+ is park and league adjusted, where 100 = average
                # Can approximate batting runs as (wRC+ - 100) * PA / 100 * some factor
                sample = team_batting[["Team", "wRC+", "PA"]].head(5).copy()
                sample["Batting_Runs_Approx"] = (
                    (sample["wRC+"] - 100) * sample["PA"] / 1000
                )
                print("Batting Runs ≈ (wRC+ - 100) * PA / 1000 (rough approximation)")
                print(sample.to_string())
                print()
            elif "Off" in team_batting.columns:
                print("Using 'Off' column as batting runs:")
                sample = team_batting[["Team", "Off"]].head(5)
                print(sample.to_string())
                print()
            else:
                print("Cannot approximate batting runs - missing wRC+ or Off columns")
                print()

        # Check for age data
        print("3. Testing age calculation:")
        # Age might not be in team stats, might need individual player data
        if team_batting is not None and "Age" in team_batting.columns:
            sample = team_batting[["Team", "Age"]].head(5)
            print("Team batting age:")
            print(sample.to_string())
            print()
        else:
            print(
                "Age not found in team batting data - may need individual player aggregation"
            )
            print()

        print("\n" + "=" * 70)

        # Analysis of missing data that we'd need to calculate
        print("MISSING DATA ANALYSIS")
        print("=" * 70)

        missing_data_sources = {
            "Bullpen xFIP": "Need to aggregate individual relief pitcher xFIP values",
            "Baserunning Runs": "May need individual player baserunning stats aggregated",
            "Defensive Runs": "May need individual player defensive stats aggregated",
            "Payroll": "External data source (e.g., Spotrac, Cot's contracts)",
            "Team Age": "May need individual batter ages aggregated",
            "Expected Wins from WAR": "Need to aggregate individual player WAR values",
        }

        print("Data we likely cannot get directly from pybaseball team functions:")
        for item, solution in missing_data_sources.items():
            print(f"  • {item}: {solution}")

        print()
        print("Potential approach:")
        print("1. Use team batting/pitching/fielding for available stats")
        print("2. Aggregate individual player stats for missing team-level data")
        print("3. Use external data sources for payroll")
        print("4. Calculate derived stats (like expected wins from WAR)")

        print("\n" + "=" * 70)

        # Try to create a sample tNERD calculation with available data
        print("SAMPLE tNERD CALCULATION WITH AVAILABLE DATA")
        print("=" * 70)

        if team_batting is not None:
            print("Creating sample tNERD calculation using available data:")

            # Select a few teams for demonstration
            sample_teams = team_batting.head(5).copy()

            # Map available columns to tNERD components
            tnerd_sample = pd.DataFrame()
            tnerd_sample["Team"] = sample_teams["Team"]

            # Batting runs (using Off if available, otherwise wRC+ approximation)
            if "Off" in sample_teams.columns:
                tnerd_sample["Batting_Runs"] = sample_teams["Off"]
                print("✓ Using 'Off' for Batting Runs")
            elif "wRC+" in sample_teams.columns and "PA" in sample_teams.columns:
                tnerd_sample["Batting_Runs"] = (
                    (sample_teams["wRC+"] - 100) * sample_teams["PA"] / 1000
                )
                print("~ Using wRC+ approximation for Batting Runs")
            else:
                tnerd_sample["Batting_Runs"] = 0  # Placeholder
                print("✗ Cannot calculate Batting Runs")

            # HR%
            if "HR" in sample_teams.columns and "AB" in sample_teams.columns:
                tnerd_sample["HR_Rate"] = sample_teams["HR"] / sample_teams["AB"]
                print("✓ Using HR/AB for HR Rate")
            elif "HR" in sample_teams.columns and "PA" in sample_teams.columns:
                tnerd_sample["HR_Rate"] = sample_teams["HR"] / sample_teams["PA"]
                print("~ Using HR/PA for HR Rate")
            else:
                tnerd_sample["HR_Rate"] = 0.030  # Placeholder average
                print("✗ Using placeholder for HR Rate")

            # Placeholders for missing data
            tnerd_sample["Baserunning_Runs"] = 0  # Placeholder
            tnerd_sample["Bullpen_xFIP"] = 4.20  # Placeholder league average
            tnerd_sample["Defensive_Runs"] = 0  # Placeholder
            tnerd_sample["Payroll"] = 150.0  # Placeholder average
            tnerd_sample["Age"] = 28.5  # Placeholder average
            tnerd_sample["Luck"] = 0.0  # Placeholder

            print("\nSample team data for tNERD calculation:")
            print(tnerd_sample.to_string())

            # Calculate sample z-scores (would need league averages and std devs)
            print("\nNote: Full tNERD calculation would require:")
            print("1. League averages and standard deviations for z-score calculation")
            print("2. Complete data for all 8 components")
            print("3. Proper handling of caps and positive-only adjustments")

        print("\n" + "=" * 70)
        print("CONCLUSION")
        print("=" * 70)

        print("Summary of findings:")
        print(
            "• Team batting, pitching, and fielding data are available from pybaseball"
        )
        print(
            "• Some tNERD components can be calculated directly (HR%, partial batting runs)"
        )
        print("• Several components require individual player data aggregation:")
        print("  - Bullpen xFIP (aggregate relief pitchers)")
        print("  - Baserunning Runs (aggregate player baserunning)")
        print("  - Defensive Runs (aggregate player defense)")
        print("  - Team Age (aggregate batter ages)")
        print("  - Expected Wins from WAR (aggregate player WAR)")
        print("• Payroll data requires external sources")
        print()
        print("Next steps:")
        print("1. Implement team data retrieval using available pybaseball functions")
        print(
            "2. Create functions to aggregate individual player data for missing components"
        )
        print("3. Research external payroll data sources")
        print("4. Implement complete tNERD calculation pipeline")

    except Exception as e:
        print(f"Error: {e}")
        # Import here since this is an error handling path
        import traceback  # noqa: PLC0415

        traceback.print_exc()


if __name__ == "__main__":
    test_detailed_team_stats()
