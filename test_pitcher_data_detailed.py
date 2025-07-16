#!/usr/bin/env python3
"""Detailed test script to explore pitcher statistics data mapping for pNERD calculation."""

import pandas as pd
import pybaseball as pb


def test_detailed_pitcher_stats():
    """Test detailed mapping of pitcher statistics for pNERD calculation."""

    print("Detailed Pitcher Statistics Analysis for pNERD Calculation")
    print("=" * 70)

    # Get 2024 pitcher data
    try:
        pitcher_stats = pb.pitching_stats(2024, qual=20)
        print(f"Retrieved {len(pitcher_stats)} pitcher records from 2024")

        # Focus on starting pitchers
        starters = pitcher_stats[pitcher_stats["GS"] > 0]
        print(f"Starting pitchers (GS > 0): {len(starters)}")
        print()

        # Required stats for pNERD and what we found
        pnerd_mapping = {
            "xFIP-": {
                "description": "xFIP minus (normalized)",
                "found_column": "xFIP-" if "xFIP-" in starters.columns else None,
                "alternatives": (
                    ["xFIP", "FIP-", "FIP"] if "xFIP" in starters.columns else None
                ),
            },
            "SwStr%": {
                "description": "Swinging-Strike Rate",
                "found_column": "SwStr%" if "SwStr%" in starters.columns else None,
                "alternatives": None,
            },
            "Strike%": {
                "description": "Strike Rate",
                "found_column": None,
                "alternatives": (
                    ["F-Strike%", "CStr%", "CSW%"]
                    if any(
                        col in starters.columns
                        for col in ["F-Strike%", "CStr%", "CSW%"]
                    )
                    else None
                ),
            },
            "Velocity": {
                "description": "Average Velocity",
                "found_column": None,
                "alternatives": (
                    ["FBv", "vFA (pi)", "vFA (sc)"]
                    if any(
                        col in starters.columns
                        for col in ["FBv", "vFA (pi)", "vFA (sc)"]
                    )
                    else None
                ),
            },
            "Age": {
                "description": "Age",
                "found_column": "Age" if "Age" in starters.columns else None,
                "alternatives": None,
            },
            "Pace": {
                "description": "Pace",
                "found_column": "Pace" if "Pace" in starters.columns else None,
                "alternatives": (
                    ["Pace (pi)"] if "Pace (pi)" in starters.columns else None
                ),
            },
            "Luck": {
                "description": "ERA- minus xFIP- (Luck)",
                "found_column": None,
                "alternatives": (
                    ["ERA-", "xFIP-", "ERA", "xFIP"]
                    if all(col in starters.columns for col in ["ERA-", "xFIP-"])
                    else None
                ),
            },
            "KN%": {
                "description": "Knuckleball Rate",
                "found_column": "KN%" if "KN%" in starters.columns else None,
                "alternatives": (
                    ["KN% (sc)", "KN% (pi)"]
                    if any(col in starters.columns for col in ["KN% (sc)", "KN% (pi)"])
                    else None
                ),
            },
        }

        print("pNERD Statistics Mapping:")
        print("-" * 50)

        for stat, info in pnerd_mapping.items():
            print(f"\n{stat} ({info['description']}):")
            if info["found_column"]:
                print(f"  ✓ Exact match: {info['found_column']}")
            elif info["alternatives"]:
                print(f"  ~ Alternatives: {info['alternatives']}")
            else:
                print("  ✗ Not found")

        print("\n" + "=" * 70)

        # Show sample data for key columns
        print("Sample data for starting pitchers:")

        # Build list of available columns to show
        columns_to_show = []
        for _stat, info in pnerd_mapping.items():
            if info["found_column"] and info["found_column"] in starters.columns:
                columns_to_show.append(info["found_column"])
            elif info["alternatives"]:
                for alt in info["alternatives"]:
                    if alt in starters.columns:
                        columns_to_show.append(alt)
                        break

        # Add some basic info columns
        basic_cols = ["Name", "Team", "IP", "GS", "ERA"]
        for col in basic_cols:
            if col in starters.columns and col not in columns_to_show:
                columns_to_show.insert(0, col)

        print(f"Showing columns: {columns_to_show}")
        print(starters[columns_to_show].head(10).to_string())

        print("\n" + "=" * 70)

        # Test calculating Luck (ERA- minus xFIP-)
        if "ERA-" in starters.columns and "xFIP-" in starters.columns:
            print("Testing Luck calculation (ERA- minus xFIP-):")
            sample = starters[["Name", "Team", "ERA-", "xFIP-"]].head(5).copy()
            sample["Luck"] = sample["ERA-"] - sample["xFIP-"]
            print(sample.to_string())
            print()

        # Test velocity data from different sources
        print("Velocity data analysis:")
        velocity_cols = [
            col
            for col in starters.columns
            if "v" in col.lower() and any(x in col for x in ["FA", "FB"])
        ]
        if velocity_cols:
            print(f"Found velocity columns: {velocity_cols}")
            sample_vel = starters[["Name", "Team"] + velocity_cols[:3]].head(5)
            print(sample_vel.to_string())
        else:
            print("No velocity columns found")

        print("\n" + "=" * 70)

        # Test strike rate alternatives
        print("Strike rate alternatives analysis:")
        strike_cols = [
            col
            for col in starters.columns
            if "strike" in col.lower() or "str" in col.lower()
        ]
        if strike_cols:
            print(f"Found strike-related columns: {strike_cols[:5]}...")  # Limit output
            sample_strike = starters[
                ["Name", "Team", "F-Strike%", "CStr%", "CSW%"]
            ].head(5)
            print(sample_strike.to_string())
        else:
            print("No strike-related columns found")

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def test_statcast_velocity():
    """Test getting velocity data from Statcast."""

    print("\n" + "=" * 70)
    print("Testing Statcast velocity data:")
    print("-" * 30)

    try:
        # Get some recent Statcast data (smaller date range)
        statcast_data = pb.statcast("2024-04-01", "2024-04-03")
        print(f"Retrieved {len(statcast_data)} Statcast records")

        # Look for velocity columns
        velocity_cols = [
            col
            for col in statcast_data.columns
            if "velocity" in col.lower() or "velo" in col.lower()
        ]
        print(f"Velocity columns: {velocity_cols}")

        if (
            velocity_cols
            and len(statcast_data) > 0
            and "player_name" in statcast_data.columns
            and "release_speed" in statcast_data.columns
        ):
            # Filter for starting pitchers and group by pitcher
            pitcher_velo = (
                statcast_data.groupby("player_name")["release_speed"]
                .mean()
                .reset_index()
            )
            pitcher_velo.columns = ["Name", "Avg_Velocity"]
            pitcher_velo = pitcher_velo.sort_values("Avg_Velocity", ascending=False)

            print("\nTop 10 pitchers by average velocity:")
            print(pitcher_velo.head(10).to_string())

        return True

    except Exception as e:
        print(f"Error getting Statcast data: {e}")
        return False


if __name__ == "__main__":
    success1 = test_detailed_pitcher_stats()
    success2 = test_statcast_velocity()

    if success1 and success2:
        print("\n✓ All tests completed successfully!")
    else:
        print("\n~ Tests completed with some issues")