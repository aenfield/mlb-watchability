#!/usr/bin/env python3

# skip linting and typing checks since this is a quickie script for understanding the data and API
# ruff: skip-file
# type: ignore
"""Detailed test script to explore pitcher statistics data mapping for pNERD calculation."""

import pandas as pd
import pybaseball as pb


def test_detailed_pitcher_stats():
    """Test detailed mapping of pitcher statistics for pNERD calculation."""

    print("Detailed Pitcher Statistics Analysis for pNERD Calculation")
    print("=" * 70)

    try:
        pitcher_stats = pb.pitching_stats(2024, qual=20)
        print(f"Retrieved {len(pitcher_stats)} pitcher records")

        # Focus on starting pitchers
        starters = pitcher_stats[pitcher_stats["GS"] > 0]
        print(f"Starting pitchers (GS > 0): {len(starters)}")
        print()

        # Updated pNERD mapping based on vision-and-reqs.md specifications
        pnerd_mapping = {
            "xFIP-": {
                "description": "xFIP minus (normalized)",
                "found_column": "xFIP-" if "xFIP-" in starters.columns else None,
                "calculation": "Direct from pybaseball",
            },
            "SwStr%": {
                "description": "Swinging-Strike Rate",
                "found_column": "SwStr%" if "SwStr%" in starters.columns else None,
                "calculation": "Direct from pybaseball",
            },
            "Strike Rate": {
                "description": "Strike Rate (calculated from Strikes/Pitches)",
                "found_column": None,
                "calculation": "Strikes / Pitches",
                "required_columns": ["Strikes", "Pitches"],
            },
            "vFA": {
                "description": "Four-seam fastball velocity",
                "found_column": "vFA" if "vFA" in starters.columns else None,
                "calculation": "Direct from pybaseball (vFA stat)",
                "alternatives": (
                    ["vFA (pi)", "vFA (sc)", "FBv"]
                    if any(
                        col in starters.columns
                        for col in ["vFA (pi)", "vFA (sc)", "FBv"]
                    )
                    else None
                ),
            },
            "Age": {
                "description": "Age",
                "found_column": "Age" if "Age" in starters.columns else None,
                "calculation": "Direct from pybaseball",
            },
            "Pace": {
                "description": "Pace",
                "found_column": "Pace" if "Pace" in starters.columns else None,
                "calculation": "Direct from pybaseball",
            },
            "Luck": {
                "description": "ERA- minus xFIP- (Luck)",
                "found_column": None,
                "calculation": "ERA- - xFIP-",
                "required_columns": ["ERA-", "xFIP-"],
            },
            "KN%": {
                "description": "Knuckleball Rate (handle NaN as 0)",
                "found_column": "KN%" if "KN%" in starters.columns else None,
                "calculation": "Direct from pybaseball, NaN -> 0",
            },
        }

        print("pNERD Statistics Mapping (Updated per vision-and-reqs.md):")
        print("-" * 60)

        for stat, info in pnerd_mapping.items():
            print(f"\n{stat} ({info['description']}):")
            if info["found_column"]:
                print(f"  ✓ Found: {info['found_column']}")
            elif "required_columns" in info:
                required = info["required_columns"]
                available = [col for col in required if col in starters.columns]
                if len(available) == len(required):
                    print(f"  ✓ Can calculate: {info['calculation']}")
                    print(f"    Using: {available}")
                else:
                    missing = [col for col in required if col not in starters.columns]
                    print(f"  ✗ Cannot calculate: missing {missing}")
            elif info.get("alternatives"):
                available_alts = [
                    alt for alt in info["alternatives"] if alt in starters.columns
                ]
                if available_alts:
                    print(f"  ~ Alternative found: {available_alts[0]}")
                    print(f"    All alternatives: {available_alts}")
                else:
                    print("  ✗ Not found (no alternatives available)")
            else:
                print("  ✗ Not found")

        print("\n" + "=" * 70)

        # Test specific calculations
        print("Testing specific calculations:")
        print("-" * 40)

        # Test Strike Rate calculation
        if "Strikes" in starters.columns and "Pitches" in starters.columns:
            print("✓ Strike Rate calculation (Strikes/Pitches):")
            sample = starters[["Name", "Team", "Strikes", "Pitches"]].head(5).copy()
            sample["Strike_Rate"] = sample["Strikes"] / sample["Pitches"]
            print(sample.to_string())
            print()

        # Test Luck calculation
        if "ERA-" in starters.columns and "xFIP-" in starters.columns:
            print("✓ Luck calculation (ERA- minus xFIP-):")
            sample = starters[["Name", "Team", "ERA-", "xFIP-"]].head(5).copy()
            sample["Luck"] = sample["ERA-"] - sample["xFIP-"]
            print(sample.to_string())
            print()

        # Test KN% NaN handling
        if "KN%" in starters.columns:
            print("✓ KN% NaN handling:")
            sample = starters[["Name", "Team", "KN%"]].head(10).copy()
            sample["KN%_cleaned"] = sample["KN%"].fillna(0)
            nan_count = sample["KN%"].isna().sum()
            print(f"Pitchers with NaN KN%: {nan_count} out of {len(sample)}")
            print(sample.to_string())
            print()

        # Test vFA velocity (and alternatives)
        velocity_cols = ["vFA", "vFA (pi)", "vFA (sc)", "FBv"]
        available_vel_cols = [col for col in velocity_cols if col in starters.columns]

        if available_vel_cols:
            print("✓ Four-seam fastball velocity options:")
            for col in available_vel_cols:
                sample = starters[["Name", "Team", col]].head(5).copy()
                print(f"\n{col}:")
                print(sample.to_string())
            print()
        else:
            print("✗ No velocity columns found")
            print()

        print("\n" + "=" * 70)

        # Velocity column comparison
        print("VELOCITY COLUMN COMPARISON")
        print("=" * 70)

        velocity_comparison_cols = ["vFA (pi)", "vFA (sc)", "FBv"]

        print("Data availability for velocity columns:")
        print("-" * 40)

        for col in velocity_comparison_cols:
            if col in starters.columns:
                total_pitchers = len(starters)
                non_null_count = starters[col].notna().sum()
                null_count = starters[col].isna().sum()
                percentage = (non_null_count / total_pitchers) * 100

                print(f"{col}:")
                print(f"  Total pitchers: {total_pitchers}")
                print(f"  Has data: {non_null_count} ({percentage:.1f}%)")
                print(f"  Missing data: {null_count} ({100-percentage:.1f}%)")
                print()
            else:
                print(f"{col}: Column not found in data")
                print()

        # Compare values where all three columns have data
        print("Comparison where all three velocity columns have data:")
        print("-" * 50)

        # Find pitchers with data in all three velocity columns
        has_all_velocity = starters.dropna(subset=velocity_comparison_cols)

        if len(has_all_velocity) > 0:
            print(
                f"Pitchers with data in all three velocity columns: {len(has_all_velocity)}"
            )

            # Show sample comparison
            sample_comparison = has_all_velocity[
                ["Name", "Team"] + velocity_comparison_cols
            ].head(10)
            print("\nSample comparison (first 10 pitchers):")
            print(sample_comparison.to_string())

            # Calculate differences
            print(f"\nVelocity differences analysis (n={len(has_all_velocity)}):")
            diff_pi_sc = has_all_velocity["vFA (pi)"] - has_all_velocity["vFA (sc)"]
            diff_pi_fbv = has_all_velocity["vFA (pi)"] - has_all_velocity["FBv"]
            diff_sc_fbv = has_all_velocity["vFA (sc)"] - has_all_velocity["FBv"]

            print(
                f"vFA (pi) - vFA (sc): mean={diff_pi_sc.mean():.2f}, std={diff_pi_sc.std():.2f}"
            )
            print(
                f"vFA (pi) - FBv: mean={diff_pi_fbv.mean():.2f}, std={diff_pi_fbv.std():.2f}"
            )
            print(
                f"vFA (sc) - FBv: mean={diff_sc_fbv.mean():.2f}, std={diff_sc_fbv.std():.2f}"
            )

        else:
            print("No pitchers have data in all three velocity columns")

        print("\n" + "=" * 70)

        # Complete pNERD data availability analysis
        print("COMPLETE pNERD DATA AVAILABILITY ANALYSIS")
        print("=" * 70)

        # Define the fields we need for pNERD calculation
        pnerd_fields = {
            "xFIP-": "xFIP-",
            "SwStr%": "SwStr%",
            "Strikes": "Strikes",  # For Strike Rate calculation
            "Pitches": "Pitches",  # For Strike Rate calculation
            "FBv": "FBv",  # Using FBv as primary velocity (100% coverage)
            "Age": "Age",
            "Pace": "Pace",
            "ERA-": "ERA-",  # For Luck calculation
            "KN%": "KN%",  # Will handle NaN as 0
        }

        print("Data availability for all required pNERD fields:")
        print("-" * 50)

        field_coverage = {}
        for field_name, column_name in pnerd_fields.items():
            if column_name in starters.columns:
                total_pitchers = len(starters)
                non_null_count = starters[column_name].notna().sum()
                null_count = starters[column_name].isna().sum()
                percentage = (non_null_count / total_pitchers) * 100
                field_coverage[field_name] = non_null_count

                print(f"{field_name} ({column_name}):")
                print(
                    f"  Has data: {non_null_count}/{total_pitchers} ({percentage:.1f}%)"
                )
                if null_count > 0:
                    print(f"  Missing: {null_count} ({100-percentage:.1f}%)")
                print()
            else:
                print(f"{field_name}: Column '{column_name}' not found")
                field_coverage[field_name] = 0
                print()

        # Find pitchers with complete data (excluding KN% since NaN is treated as 0)
        required_columns = [col for col in pnerd_fields.values() if col != "KN%"]

        print("Complete data analysis:")
        print("-" * 30)

        # Check for complete data in required columns
        complete_data_mask = starters[required_columns].notna().all(axis=1)
        complete_data_pitchers = starters[complete_data_mask]

        total_pitchers = len(starters)
        complete_count = len(complete_data_pitchers)
        incomplete_count = total_pitchers - complete_count

        print(f"Total starting pitchers: {total_pitchers}")
        print(
            f"Pitchers with complete pNERD data: {complete_count} ({complete_count/total_pitchers*100:.1f}%)"
        )
        print(
            f"Pitchers with incomplete data: {incomplete_count} ({incomplete_count/total_pitchers*100:.1f}%)"
        )

        if incomplete_count > 0:
            print("\nPitchers missing data by field:")
            for field_name, column_name in pnerd_fields.items():
                if column_name != "KN%" and column_name in starters.columns:
                    missing_count = starters[column_name].isna().sum()
                    if missing_count > 0:
                        missing_pitchers = starters[starters[column_name].isna()][
                            "Name"
                        ].tolist()
                        print(f"  {field_name}: {missing_count} pitchers missing")
                        if (
                            missing_count <= 10  # noqa: PLR2004
                        ):  # Show names if not too many
                            print(f"    {missing_pitchers}")

        # Show sample of complete data pitchers
        if complete_count > 0:
            print("\nSample of pitchers with complete pNERD data (first 10):")
            display_cols = ["Name", "Team", "GS", "IP"] + required_columns
            sample_complete = complete_data_pitchers[display_cols].head(10)
            print(sample_complete.to_string())

        # Handle KN% separately since NaN is treated as 0
        print("\nKN% special handling:")
        kn_non_null = starters["KN%"].notna().sum()
        kn_null = starters["KN%"].isna().sum()
        print(
            f"  KN% has actual data: {kn_non_null}/{total_pitchers} ({kn_non_null/total_pitchers*100:.1f}%)"
        )
        print(
            f"  KN% will be set to 0: {kn_null}/{total_pitchers} ({kn_null/total_pitchers*100:.1f}%)"
        )
        print(f"  Effective KN% coverage: {total_pitchers}/{total_pitchers} (100.0%)")

        print("\n" + "=" * 70)

        # Focus on specific pitchers: Tarik Skubal and Matt Waldron
        print("SPECIFIC PITCHER ANALYSIS")
        print("=" * 70)

        target_pitchers = ["Tarik Skubal", "Matt Waldron"]

        for pitcher_name in target_pitchers:
            pitcher_data = starters[starters["Name"] == pitcher_name]

            if len(pitcher_data) > 0:
                print(f"\n{pitcher_name.upper()} - Detailed pNERD Statistics:")
                print("-" * 50)

                pitcher_row = pitcher_data.iloc[0]

                # Display all required stats for this pitcher
                print(f"Name: {pitcher_row.get('Name', 'N/A')}")
                print(f"Team: {pitcher_row.get('Team', 'N/A')}")
                print(f"Games Started: {pitcher_row.get('GS', 'N/A')}")
                print(f"Innings Pitched: {pitcher_row.get('IP', 'N/A')}")
                print()

                print("pNERD Component Statistics:")
                print(f"  xFIP-: {pitcher_row.get('xFIP-', 'N/A')}")
                print(f"  SwStr%: {pitcher_row.get('SwStr%', 'N/A')}")

                # Calculate Strike Rate
                if "Strikes" in pitcher_row and "Pitches" in pitcher_row:
                    strike_rate = pitcher_row["Strikes"] / pitcher_row["Pitches"]
                    print(
                        f"  Strike Rate: {strike_rate:.3f} (calculated from {pitcher_row['Strikes']} strikes / {pitcher_row['Pitches']} pitches)"
                    )
                else:
                    print("  Strike Rate: Cannot calculate (missing Strikes/Pitches)")

                # Show all available velocity columns
                velocity_cols = ["vFA", "vFA (pi)", "vFA (sc)", "FBv"]
                available_velocity = []

                for col in velocity_cols:
                    if col in pitcher_row and not pd.isna(pitcher_row[col]):
                        available_velocity.append(f"{col}: {pitcher_row[col]} mph")

                if available_velocity:
                    print("  Velocity options:")
                    for vel_info in available_velocity:
                        print(f"    {vel_info}")
                else:
                    print("  vFA (velocity): N/A mph (no velocity data available)")
                print(f"  Age: {pitcher_row.get('Age', 'N/A')}")
                print(f"  Pace: {pitcher_row.get('Pace', 'N/A')} seconds")

                # Calculate Luck
                if "ERA-" in pitcher_row and "xFIP-" in pitcher_row:
                    luck = pitcher_row["ERA-"] - pitcher_row["xFIP-"]
                    print(
                        f"  Luck: {luck:.1f} (calculated from {pitcher_row['ERA-']} ERA- - {pitcher_row['xFIP-']} xFIP-)"
                    )
                else:
                    print("  Luck: Cannot calculate (missing ERA- or xFIP-)")

                # Handle KN% with NaN
                kn_rate = pitcher_row.get("KN%", 0)
                if pd.isna(kn_rate):
                    kn_rate = 0
                print(f"  KN%: {kn_rate} (NaN treated as 0)")

                print()

                # Show all available columns for this pitcher
                # print("All available statistics for this pitcher:")
                # for col in sorted(starters.columns):
                #     value = pitcher_row.get(col, 'N/A')
                #     if pd.isna(value):
                #         value = 'NaN'
                #     print(f"  {col}: {value}")

                print("\n" + "=" * 50)

            else:
                print(f"\n{pitcher_name.upper()}: Not found in starting pitchers data")
                # Try to find similar names
                similar = starters[
                    starters["Name"].str.contains(
                        pitcher_name.split()[-1], case=False, na=False
                    )
                ]
                if len(similar) > 0:
                    print(f"  Similar names found: {similar['Name'].tolist()}")
                print()

        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)

        # Summary of data availability
        available_stats = []
        missing_stats = []

        for stat, info in pnerd_mapping.items():
            if info["found_column"]:
                available_stats.append(stat)
            elif "required_columns" in info:
                required = info["required_columns"]
                if all(col in starters.columns for col in required):
                    available_stats.append(stat)
                else:
                    missing_stats.append(stat)
            elif info.get("alternatives"):
                available_alts = [
                    alt for alt in info["alternatives"] if alt in starters.columns
                ]
                if available_alts:
                    available_stats.append(stat)
                else:
                    missing_stats.append(stat)
            else:
                missing_stats.append(stat)

        print(f"Available pNERD statistics: {len(available_stats)}")
        for stat in available_stats:
            print(f"  ✓ {stat}")

        print(f"\nMissing pNERD statistics: {len(missing_stats)}")
        for stat in missing_stats:
            print(f"  ✗ {stat}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_detailed_pitcher_stats()
