#!/usr/bin/env python3

# Script to lookup player IDs using MLBAM ID and pybaseball's playerid_reverse_lookup
# ruff: skip-file
# type: ignore

import sys
from pathlib import Path
import pandas as pd

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pybaseball as pb


def lookup_player_by_mlbam_id(mlbam_id: int):
    """
    Look up a player by MLBAM ID using pybaseball's playerid_reverse_lookup function.
    
    Args:
        mlbam_id: MLB Advanced Media ID (integer)
    """
    print(f"Looking up player with MLBAM ID: {mlbam_id}")
    print("=" * 60)
    
    try:
        # Use playerid_reverse_lookup to get all IDs for this MLBAM ID
        print("🔍 Performing reverse lookup...")
        lookup_results = pb.playerid_reverse_lookup([mlbam_id], key_type='mlbam')
        
        if not lookup_results.empty:
            print(f"✅ Found player data for MLBAM ID {mlbam_id}")
            display_player_ids(lookup_results.iloc[0], mlbam_id)
            
            # Try to get current stats using the player name
            player_name = f"{lookup_results.iloc[0].get('name_first', '')} {lookup_results.iloc[0].get('name_last', '')}".strip()
            # if player_name.strip():
            #     get_current_stats(player_name)
            
        else:
            print(f"❌ No player found with MLBAM ID {mlbam_id}")
            print("   This could mean:")
            print("   • Invalid MLBAM ID")
            print("   • Player not in Chadwick Bureau database")
            print("   • Very recent player not yet indexed")
        
    except Exception as e:
        print(f"❌ Lookup failed: {e}")
        import traceback
        traceback.print_exc()


def display_player_ids(player_row: pd.Series, mlbam_id: int):
    """Display all the player IDs and information from the lookup result."""
    print(f"\n🏷️  Player Information:")
    print("-" * 30)
    
    # Display basic player info
    first_name = player_row.get('name_first', 'N/A')
    last_name = player_row.get('name_last', 'N/A')
    print(f"   Name: {first_name} {last_name}")
    
    # Display career span
    first_year = player_row.get('mlb_played_first', 'N/A')
    last_year = player_row.get('mlb_played_last', 'N/A')
    print(f"   MLB Career: {first_year} - {last_year}")
    
    # Display birth info if available
    birth_year = player_row.get('birth_year', None)
    if pd.notna(birth_year):
        print(f"   Birth Year: {birth_year}")
    
    print(f"\n🆔 Cross-Database Player IDs:")
    print("-" * 35)
    
    # Show the input MLBAM ID
    print(f"   MLBAM (Input): {mlbam_id}")
    
    # Show all other ID types
    id_mappings = {
        'key_fangraphs': 'FanGraphs',
        'key_bbref': 'Baseball Reference', 
        'key_retro': 'Retrosheet',
        'key_mlbam': 'MLBAM (Confirmed)'
    }
    
    for id_column, id_name in id_mappings.items():
        if id_column in player_row.index:
            id_value = player_row.get(id_column)
            if pd.notna(id_value):
                if id_value == -1:
                    print(f"   {id_name}: Not Available (-1)")
                else:
                    print(f"   {id_name}: {id_value}")
            else:
                print(f"   {id_name}: Not Available (NaN)")
        else:
            print(f"   {id_name}: Column not found")
    
    # Show any other columns that might contain useful info
    other_columns = [col for col in player_row.index 
                    if col not in ['name_first', 'name_last', 'mlb_played_first', 'mlb_played_last', 'birth_year'] 
                    and not col.startswith('key_')]
    
    if other_columns:
        print(f"\n📋 Additional Information:")
        print("-" * 30)
        for col in other_columns:
            value = player_row.get(col)
            if pd.notna(value) and value != '':
                print(f"   {col}: {value}")


def get_current_stats(player_name: str):
    """Try to get current season pitching/batting stats for the player."""
    current_year = 2025
    
    print(f"\n📊 Current Season Stats ({current_year}):")
    print("-" * 40)
    print(f"🎯 Looking for: {player_name}")
    
    # Try to get pitching stats
    try:
        pitching_stats = pb.pitching_stats(current_year, qual=1)
        pitcher_match = pitching_stats[pitching_stats['Name'] == player_name]
        
        if not pitcher_match.empty:
            p_row = pitcher_match.iloc[0]
            print(f"   🥎 Pitching: GS={p_row.get('GS', 0)}, IP={p_row.get('IP', 0):.1f}, ERA={p_row.get('ERA', 0):.2f}, WHIP={p_row.get('WHIP', 0):.2f}")
        else:
            print(f"   🥎 Pitching: No stats found")
    except Exception as e:
        print(f"   🥎 Pitching: Error retrieving stats - {e}")
    
    # Try to get batting stats
    try:
        batting_stats = pb.batting_stats(current_year, qual=1)
        batter_match = batting_stats[batting_stats['Name'] == player_name]
        
        if not batter_match.empty:
            b_row = batter_match.iloc[0]
            print(f"   🏏 Batting: G={b_row.get('G', 0)}, AB={b_row.get('AB', 0)}, AVG={b_row.get('AVG', 0):.3f}, OPS={b_row.get('OPS', 0):.3f}")
        else:
            print(f"   🏏 Batting: No stats found")
    except Exception as e:
        print(f"   🏏 Batting: Error retrieving stats - {e}")


def main():
    """Main function to handle user input and perform lookup."""
    if len(sys.argv) > 1:
        # MLBAM ID provided as command line argument
        try:
            mlbam_id = int(sys.argv[1])
            lookup_player_by_mlbam_id(mlbam_id)
        except ValueError:
            print(f"❌ Invalid MLBAM ID: '{sys.argv[1]}' (must be an integer)")
            sys.exit(1)
    else:
        # Interactive mode
        print("MLBAM ID Reverse Lookup Tool")
        print("=" * 40)
        print("Enter MLBAM IDs to get cross-database player IDs")
        print("Examples:")
        print("  • 660271 (Shohei Ohtani)")
        print("  • 694973 (Paul Skenes)")
        print("  • 607074 (Carlos Rodón)")
        print("  • Type 'quit' to exit")
        print()
        
        while True:
            try:
                user_input = input("Enter MLBAM ID: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    print("Please enter an MLBAM ID.\n")
                    continue
                
                try:
                    mlbam_id = int(user_input)
                    print()
                    lookup_player_by_mlbam_id(mlbam_id)
                    print("\n" + "="*60 + "\n")
                except ValueError:
                    print(f"❌ Invalid MLBAM ID: '{user_input}' (must be an integer)\n")
                    continue
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break


if __name__ == "__main__":
    main()