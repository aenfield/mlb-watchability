#!/usr/bin/env python3

# Script to lookup a player using FanGraphs player lookup functionality
# ruff: skip-file
# type: ignore

import sys
from pathlib import Path
import pandas as pd

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pybaseball as pb


def lookup_player_by_name(player_name: str):
    """
    Look up a player by name using pybaseball's playerid_lookup function.
    
    Args:
        player_name: Full name or "Last, First" format
    """
    print(f"Looking up player: '{player_name}'")
    print("=" * 60)
    
    # Parse the input name
    if "," in player_name:
        # "Last, First" format
        parts = [p.strip() for p in player_name.split(",")]
        if len(parts) >= 2:
            last_name = parts[0]
            first_name = parts[1]
        else:
            last_name = parts[0]
            first_name = None
    else:
        # "First Last" or just "Last" format
        parts = player_name.strip().split()
        if len(parts) >= 2:
            first_name = parts[0]
            last_name = parts[-1]  # Take last word as last name
        elif len(parts) == 1:
            last_name = parts[0]
            first_name = None
        else:
            print("❌ Invalid player name format")
            return
    
    print(f"Searching for: Last='{last_name}', First='{first_name}'")
    print()
    
    try:
        # First, try exact lookup
        print("🔍 Trying exact lookup...")
        if first_name:
            lookup_results = pb.playerid_lookup(last_name, first_name)
        else:
            lookup_results = pb.playerid_lookup(last_name)
        
        if not lookup_results.empty:
            print(f"✅ Found {len(lookup_results)} exact match(es)")
            display_results(lookup_results, "Exact Matches")
        else:
            print("❌ No exact matches found")
        
        # If no exact matches or user wants to see fuzzy matches, try fuzzy
        if lookup_results.empty or len(lookup_results) > 10:
            print("\n🔍 Trying fuzzy lookup...")
            if first_name:
                fuzzy_results = pb.playerid_lookup(last_name, first_name, fuzzy=True)
            else:
                fuzzy_results = pb.playerid_lookup(last_name, fuzzy=True)
            
            if not fuzzy_results.empty and not fuzzy_results.equals(lookup_results):
                print(f"✅ Found {len(fuzzy_results)} fuzzy match(es)")
                display_results(fuzzy_results, "Fuzzy Matches")
            else:
                print("❌ No additional fuzzy matches found")
        
        # If we have results, try to get current stats
        # if not lookup_results.empty:
        #     print("\n📊 Attempting to get current season stats...")
        #     get_current_stats(lookup_results)
            
    except Exception as e:
        print(f"❌ Lookup failed: {e}")
        import traceback
        traceback.print_exc()


def display_results(results_df: pd.DataFrame, title: str):
    """Display the lookup results in a formatted way."""
    print(f"\n{title}:")
    print("-" * len(title))
    
    for idx, row in results_df.iterrows():
        print(f"\n🏷️  Result {idx + 1}:")
        print(f"   Name: {row.get('name_first', 'N/A')} {row.get('name_last', 'N/A')}")
        print(f"   MLB Debut: {row.get('mlb_played_first', 'N/A')} - {row.get('mlb_played_last', 'N/A')}")
        
        # Show all available ID types
        id_columns = [col for col in row.index if col.startswith('key_')]
        if id_columns:
            print(f"   Player IDs:")
            for id_col in id_columns:
                id_value = row.get(id_col)
                if pd.notna(id_value) and id_value != -1:
                    system_name = id_col.replace('key_', '').upper()
                    print(f"     {system_name}: {id_value}")
        
        # Show birth info if available
        if pd.notna(row.get('birth_year')):
            print(f"   Birth: {row.get('birth_year', 'N/A')}")
        
        print()


def get_current_stats(lookup_results: pd.DataFrame):
    """Try to get current season pitching/batting stats for the players."""
    current_year = 2025
    
    for _, player_row in lookup_results.iterrows():
        player_name = f"{player_row.get('name_first', '')} {player_row.get('name_last', '')}".strip()
        print(f"\n🎯 Stats for {player_name}:")
        
        # Try to get pitching stats
        try:
            pitching_stats = pb.pitching_stats(current_year, qual=1)
            pitcher_match = pitching_stats[pitching_stats['Name'] == player_name]
            
            if not pitcher_match.empty:
                p_row = pitcher_match.iloc[0]
                print(f"   🥎 Pitching: GS={p_row.get('GS', 0)}, IP={p_row.get('IP', 0):.1f}, ERA={p_row.get('ERA', 0):.2f}")
            else:
                print(f"   🥎 Pitching: No stats found for {current_year}")
        except Exception as e:
            print(f"   🥎 Pitching: Error retrieving stats - {e}")
        
        # Try to get batting stats
        try:
            batting_stats = pb.batting_stats(current_year, qual=1)
            batter_match = batting_stats[batting_stats['Name'] == player_name]
            
            if not batter_match.empty:
                b_row = batter_match.iloc[0]
                print(f"   🏏 Batting: G={b_row.get('G', 0)}, AB={b_row.get('AB', 0)}, AVG={b_row.get('AVG', 0):.3f}")
            else:
                print(f"   🏏 Batting: No stats found for {current_year}")
        except Exception as e:
            print(f"   🏏 Batting: Error retrieving stats - {e}")


def main():
    """Main function to handle user input and perform lookup."""
    if len(sys.argv) > 1:
        # Player name provided as command line argument
        player_name = " ".join(sys.argv[1:])
        lookup_player_by_name(player_name)
    else:
        # Interactive mode
        print("FanGraphs Player Lookup Tool")
        print("=" * 40)
        print("Enter player names in any of these formats:")
        print("  • 'First Last' (e.g., 'Shohei Ohtani')")
        print("  • 'Last, First' (e.g., 'Ohtani, Shohei')")
        print("  • 'Last' only (e.g., 'Ohtani')")
        print("  • Type 'quit' to exit")
        print()
        
        while True:
            try:
                player_name = input("Enter player name: ").strip()
                
                if player_name.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not player_name:
                    print("Please enter a player name.\n")
                    continue
                
                print()
                lookup_player_by_name(player_name)
                print("\n" + "="*60 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break


if __name__ == "__main__":
    main()