#!/usr/bin/env python3

# Script to get pitcher names, MLBAM IDs, and basic stats for today's games
# ruff: skip-file
# type: ignore

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import statsapi
import pybaseball as pb
from mlb_watchability.data_retrieval import get_game_schedule


def get_pitcher_mlbam_ids_and_stats(date: str = None):
    """Get pitcher names, MLBAM IDs, and basic stats for games on specified date."""
    
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"Getting pitcher MLBAM IDs and stats for {date}")
    print("=" * 50)
    
    try:
        # First, get the raw schedule data directly from MLB-StatsAPI
        # Convert date format for API call
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        api_date = date_obj.strftime("%m/%d/%Y")
        
        print(f"Fetching schedule data for {api_date}...")
        raw_schedule = statsapi.schedule(start_date=api_date, end_date=api_date)
        
        print(f"Found {len(raw_schedule)} games")
        print()

        # Get pitcher stats data for the current season
        print("Fetching pitcher stats from pybaseball...")
        pitcher_stats_df = pb.pitching_stats(2025, qual=1)  # Get all pitchers with at least 1 inning
        print(f"Found {len(pitcher_stats_df)} pitchers in pybaseball data")
        # print("Here's the header rows of that data:")
        # pd.set_option('display.max_columns', None)
        # print(','.join(map(str, pitcher_stats_df.columns)))
        # print(','.join(map(str, pitcher_stats_df.loc[0].values)))
        print()
        
        # Check if pybaseball data contains MLBAM IDs
        has_mlbam_ids = 'mlbam_id' in pitcher_stats_df.columns or 'key_mlbam' in pitcher_stats_df.columns
        print(f"PyBaseball data contains MLBAM IDs: {has_mlbam_ids}")
        if has_mlbam_ids:
            mlbam_col = 'mlbam_id' if 'mlbam_id' in pitcher_stats_df.columns else 'key_mlbam'
            print(f"MLBAM ID column: {mlbam_col}")
        print()
        
        all_pitcher_data = []
        
        for i, game in enumerate(raw_schedule, 1):
            print(f"Game {i}: {game.get('away_name', 'Unknown')} @ {game.get('home_name', 'Unknown')}")
            
            # Check if pitcher IDs are already in the schedule response
            away_pitcher_name = game.get("away_probable_pitcher")
            home_pitcher_name = game.get("home_probable_pitcher")
            
            away_pitcher_id = game.get("away_probable_pitcher_id")
            home_pitcher_id = game.get("home_probable_pitcher_id")
            
            print(f"  Away pitcher: {away_pitcher_name} (ID from schedule: {away_pitcher_id})")
            print(f"  Home pitcher: {home_pitcher_name} (ID from schedule: {home_pitcher_id})")
            
            # Process away pitcher
            if away_pitcher_name and away_pitcher_name != "TBD":
                pitcher_data = {
                    "name": away_pitcher_name,
                    "team": game.get('away_name', 'Unknown'),
                    "mlbam_id": away_pitcher_id,
                    "source": "schedule" if away_pitcher_id else "lookup_needed",
                    "gs": None,
                    "ip": None,
                    "pybaseball_match": None
                }
                
                # If no ID in schedule, try lookup
                if not away_pitcher_id:
                    try:
                        print(f"    Looking up MLBAM ID for {away_pitcher_name}...")
                        lookup_results = statsapi.lookup_player(away_pitcher_name)
                        if lookup_results:
                            # Try to find the best match (prefer current team if possible)
                            best_match = lookup_results[0]  # Default to first result
                            for player in lookup_results:
                                if player.get('currentTeam', {}).get('name') == game.get('away_name'):
                                    best_match = player
                                    break
                            
                            pitcher_data["mlbam_id"] = best_match.get("id")
                            pitcher_data["source"] = "lookup"
                            pitcher_data["lookup_full_name"] = best_match.get("fullName")
                            print(f"    Found: {best_match.get('fullName')} (ID: {best_match.get('id')})")
                        else:
                            print(f"    No results found for {away_pitcher_name}")
                    except Exception as e:
                        print(f"    Lookup failed for {away_pitcher_name}: {e}")
                
                all_pitcher_data.append(pitcher_data)
            
            # Process home pitcher
            if home_pitcher_name and home_pitcher_name != "TBD":
                pitcher_data = {
                    "name": home_pitcher_name,
                    "team": game.get('home_name', 'Unknown'),
                    "mlbam_id": home_pitcher_id,
                    "source": "schedule" if home_pitcher_id else "lookup_needed",
                    "gs": None,
                    "ip": None,
                    "pybaseball_match": None
                }
                
                # If no ID in schedule, try lookup
                if not home_pitcher_id:
                    try:
                        print(f"    Looking up MLBAM ID for {home_pitcher_name}...")
                        lookup_results = statsapi.lookup_player(home_pitcher_name)
                        if lookup_results:
                            # Try to find the best match (prefer current team if possible)
                            best_match = lookup_results[0]  # Default to first result
                            for player in lookup_results:
                                if player.get('currentTeam', {}).get('name') == game.get('home_name'):
                                    best_match = player
                                    break
                            
                            pitcher_data["mlbam_id"] = best_match.get("id")
                            pitcher_data["source"] = "lookup"
                            pitcher_data["lookup_full_name"] = best_match.get("fullName")
                            print(f"    Found: {best_match.get('fullName')} (ID: {best_match.get('id')})")
                        else:
                            print(f"    No results found for {home_pitcher_name}")
                    except Exception as e:
                        print(f"    Lookup failed for {home_pitcher_name}: {e}")
                
                all_pitcher_data.append(pitcher_data)
            
            print()
        
        # Now try both name matching and FanGraphs ID matching for each pitcher
        print("Testing both name matching and FanGraphs ID matching for today's pitchers...")
        print("=" * 80)
        
        for pitcher in all_pitcher_data:
            print(f"\n{pitcher['name']} (MLBAM ID: {pitcher['mlbam_id']})")
            
            if not pitcher["mlbam_id"]:
                print("  ⚠ Skipping - no MLBAM ID")
                continue
            
            # Initialize results for both methods
            name_match_result = None
            fangraphs_match_result = None
            
            # METHOD 1: Direct name matching
            print("  Method 1 - Name matching:")
            name_matches = pitcher_stats_df[pitcher_stats_df["Name"] == pitcher["name"]]
            if not name_matches.empty:
                match_row = name_matches.iloc[0]
                name_match_result = {
                    "gs": match_row.get("GS", 0),
                    "ip": match_row.get("IP", 0.0),
                    "method": "exact_name"
                }
                print(f"    ✓ Found by exact name: GS={name_match_result['gs']}, IP={name_match_result['ip']:.1f}")
            else:
                print("    ✗ No exact name match found")
            
            # METHOD 2: FanGraphs ID lookup via MLBAM ID
            print("  Method 2 - FanGraphs ID lookup:")
            try:
                # Use playerid_reverse_lookup to get FanGraphs ID from MLBAM ID
                id_lookup = pb.playerid_reverse_lookup([pitcher["mlbam_id"]], key_type='mlbam')
                
                if not id_lookup.empty and 'key_fangraphs' in id_lookup.columns:
                    fangraphs_id = id_lookup['key_fangraphs'].iloc[0]
                    print(f"    → Found FanGraphs ID: {fangraphs_id}")
                    
                    if pd.notna(fangraphs_id):
                        # Check if pybaseball data has FanGraphs ID column
                        if 'playerid' in pitcher_stats_df.columns:
                            fg_matches = pitcher_stats_df[pitcher_stats_df['playerid'] == fangraphs_id]
                        elif 'IDfg' in pitcher_stats_df.columns:
                            fg_matches = pitcher_stats_df[pitcher_stats_df['IDfg'] == fangraphs_id]
                        else:
                            fg_matches = pd.DataFrame()  # Empty if no FG ID column
                            print("    ✗ No FanGraphs ID column found in pitcher stats")
                        
                        if not fg_matches.empty:
                            match_row = fg_matches.iloc[0]
                            fangraphs_match_result = {
                                "gs": match_row.get("GS", 0),
                                "ip": match_row.get("IP", 0.0),
                                "method": "fangraphs_id"
                            }
                            print(f"    ✓ Found by FanGraphs ID: GS={fangraphs_match_result['gs']}, IP={fangraphs_match_result['ip']:.1f}")
                        else:
                            print("    ✗ No match found using FanGraphs ID")
                    else:
                        print("    ✗ FanGraphs ID is null/NaN")
                else:
                    print("    ✗ No FanGraphs ID found in lookup result")
                    
            except Exception as e:
                print(f"    ✗ FanGraphs lookup failed: {e}")
            
            # Store results in pitcher data
            pitcher["name_match"] = name_match_result
            pitcher["fangraphs_match"] = fangraphs_match_result
            
            # Use the best available match for final stats
            if name_match_result:
                pitcher["gs"] = name_match_result["gs"]
                pitcher["ip"] = name_match_result["ip"]
                pitcher["pybaseball_match"] = name_match_result["method"]
            elif fangraphs_match_result:
                pitcher["gs"] = fangraphs_match_result["gs"]
                pitcher["ip"] = fangraphs_match_result["ip"]
                pitcher["pybaseball_match"] = fangraphs_match_result["method"]
            else:
                pitcher["gs"] = None
                pitcher["ip"] = None
                pitcher["pybaseball_match"] = None
            
            # Compare results if both methods found data
            if name_match_result and fangraphs_match_result:
                if (name_match_result["gs"] == fangraphs_match_result["gs"] and 
                    abs(name_match_result["ip"] - fangraphs_match_result["ip"]) < 0.1):
                    print("    ✅ Both methods agree!")
                else:
                    print(f"    ⚠ Methods disagree! Name: GS={name_match_result['gs']}, IP={name_match_result['ip']:.1f} vs FG: GS={fangraphs_match_result['gs']}, IP={fangraphs_match_result['ip']:.1f}")
            elif name_match_result and not fangraphs_match_result:
                print("    → Only name matching worked")
            elif fangraphs_match_result and not name_match_result:
                print("    → Only FanGraphs ID matching worked")
            else:
                print("    ✗ Neither method found a match")
        
        print()
        
        # Summary
        print("SUMMARY")
        print("=" * 50)
        print(f"Total pitchers found: {len(all_pitcher_data)}")
        
        ids_from_schedule = len([p for p in all_pitcher_data if p["source"] == "schedule"])
        ids_from_lookup = len([p for p in all_pitcher_data if p["source"] == "lookup"])
        missing_ids = len([p for p in all_pitcher_data if not p["mlbam_id"]])
        
        stats_matches = len([p for p in all_pitcher_data if p["pybaseball_match"] is not None])
        stats_missing = len([p for p in all_pitcher_data if p["pybaseball_match"] is None])
        
        print(f"IDs from schedule: {ids_from_schedule}")
        print(f"IDs from lookup: {ids_from_lookup}")
        print(f"Missing IDs: {missing_ids}")
        print(f"PyBaseball matches: {stats_matches}")
        print(f"PyBaseball missing: {stats_missing}")
        print()
        
        # Show all pitcher data
        print("ALL PITCHER DATA")
        print("=" * 50)
        for pitcher in all_pitcher_data:
            id_status = f"MLBAM ID: {pitcher['mlbam_id']}" if pitcher['mlbam_id'] else "NO ID"
            print(f"{pitcher['name']} ({pitcher['team']}) - {id_status} [{pitcher['source']}]")
            if pitcher.get('lookup_full_name') and pitcher['lookup_full_name'] != pitcher['name']:
                print(f"  Full name from lookup: {pitcher['lookup_full_name']}")
            if pitcher['pybaseball_match']:
                print(f"  PyBaseball: GS={pitcher['gs']}, IP={pitcher['ip']:.1f} [{pitcher['pybaseball_match']}]")
            else:
                print("  PyBaseball: No match found")
        
        print()
        print("GAMES STARTED (GS) AND INNINGS PITCHED (IP) FOR TODAY'S PITCHERS")
        print("=" * 70)
        for pitcher in all_pitcher_data:
            if pitcher['gs'] is not None and pitcher['ip'] is not None:
                print(f"{pitcher['name']:<25} GS: {pitcher['gs']:>2}, IP: {pitcher['ip']:>5.1f}")
            else:
                print(f"{pitcher['name']:<25} GS: --, IP: -----")
        
        return all_pitcher_data
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    # Use today's date or pass a date as command line argument
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    else:
        target_date = datetime.now().strftime("%Y-%m-%d")
    
    pitcher_data = get_pitcher_mlbam_ids_and_stats(target_date)