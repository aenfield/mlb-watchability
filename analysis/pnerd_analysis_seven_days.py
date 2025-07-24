#!/usr/bin/env python3
"""
Analysis script to examine pNERD scores over the last seven days.

This script pulls games and starting pitchers for the last seven days before today,
calculates pNERD scores for each pitcher, and provides detailed statistics to
understand the distribution and range of pNERD scores.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# Add the src directory to the Python path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mlb_watchability.data_retrieval import get_game_schedule
from mlb_watchability.pitcher_stats import (
    calculate_detailed_pitcher_nerd_scores,
    find_pitcher_nerd_stats_fuzzy,
)


def get_last_seven_days() -> list[str]:
    """Get list of dates for the last seven days before today."""
    today = datetime.now().date()
    dates = []
    for i in range(1, 8):  # Days 1-7 before today
        date = today - timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
    return dates


def collect_games_and_pitchers(dates: list[str]) -> list[dict]:
    """
    Collect games and starting pitchers for the given dates.
    
    Returns a list of dictionaries with date, game, and pitcher information.
    """
    game_pitcher_data = []
    
    for date in dates:
        print(f"Fetching games for {date}...")
        try:
            games = get_game_schedule(date)
            
            for game in games:
                # Add away pitcher if available
                if game["away_starter"]:
                    game_pitcher_data.append({
                        "date": date,
                        "away_team": game["away_team"],
                        "home_team": game["home_team"],
                        "time": game["time"],
                        "pitcher_name": game["away_starter"],
                        "pitcher_team": game["away_team"],
                        "pitcher_role": "away"
                    })
                
                # Add home pitcher if available
                if game["home_starter"]:
                    game_pitcher_data.append({
                        "date": date,
                        "away_team": game["away_team"],
                        "home_team": game["home_team"],
                        "time": game["time"],
                        "pitcher_name": game["home_starter"],
                        "pitcher_team": game["home_team"],
                        "pitcher_role": "home"
                    })
                    
        except Exception as e:
            print(f"Error fetching games for {date}: {e}")
            continue
    
    return game_pitcher_data


def add_pnerd_scores(game_pitcher_data: list[dict]) -> pd.DataFrame:
    """
    Add pNERD scores to the game/pitcher data and return as DataFrame.
    """
    print("Calculating pNERD scores for all pitchers...")
    
    # Get detailed pNERD statistics for all pitchers
    pitcher_nerd_stats = calculate_detailed_pitcher_nerd_scores(2025)
    
    # Add pNERD data to each game/pitcher row
    for row in game_pitcher_data:
        pitcher_name = row["pitcher_name"]
        
        # Find pitcher stats using fuzzy matching
        nerd_stats = find_pitcher_nerd_stats_fuzzy(pitcher_nerd_stats, pitcher_name)
        
        if nerd_stats:
            row["pnerd_score"] = nerd_stats.pnerd_score
            row["xfip_minus"] = nerd_stats.pitcher_stats.xfip_minus
            row["swinging_strike_rate"] = nerd_stats.pitcher_stats.swinging_strike_rate
            row["strike_rate"] = nerd_stats.pitcher_stats.strike_rate
            row["velocity"] = nerd_stats.pitcher_stats.velocity
            row["age"] = nerd_stats.pitcher_stats.age
            row["pace"] = nerd_stats.pitcher_stats.pace
            row["luck"] = nerd_stats.pitcher_stats.luck
            row["knuckleball_rate"] = nerd_stats.pitcher_stats.knuckleball_rate
            
            # Add component breakdowns
            row["xfip_component"] = nerd_stats.xfip_component
            row["swinging_strike_component"] = nerd_stats.swinging_strike_component
            row["strike_component"] = nerd_stats.strike_component
            row["velocity_component"] = nerd_stats.velocity_component
            row["age_component"] = nerd_stats.age_component
            row["pace_component"] = nerd_stats.pace_component
            row["luck_component"] = nerd_stats.luck_component
            row["knuckleball_component"] = nerd_stats.knuckleball_component
            row["constant_component"] = nerd_stats.constant_component
        else:
            # Mark as missing data
            row["pnerd_score"] = None
            row["xfip_minus"] = None
            row["swinging_strike_rate"] = None
            row["strike_rate"] = None
            row["velocity"] = None
            row["age"] = None
            row["pace"] = None
            row["luck"] = None
            row["knuckleball_rate"] = None
            row["xfip_component"] = None
            row["swinging_strike_component"] = None
            row["strike_component"] = None
            row["velocity_component"] = None
            row["age_component"] = None
            row["pace_component"] = None
            row["luck_component"] = None
            row["knuckleball_component"] = None
            row["constant_component"] = None
    
    # Convert to DataFrame
    df = pd.DataFrame(game_pitcher_data)
    
    return df


def analyze_pnerd_distribution(df: pd.DataFrame) -> None:
    """
    Calculate and display descriptive statistics for pNERD score distribution.
    """
    print("\n" + "="*80)
    print("PNERD SCORE DISTRIBUTION ANALYSIS")
    print("="*80)
    
    # Filter out rows with missing pNERD scores
    valid_scores = df.dropna(subset=["pnerd_score"])
    
    print(f"\nData Summary:")
    print(f"  Total game/pitcher combinations: {len(df)}")
    print(f"  Pitchers with pNERD scores: {len(valid_scores)}")
    print(f"  Missing pNERD scores: {len(df) - len(valid_scores)}")
    
    if len(valid_scores) == 0:
        print("\nNo valid pNERD scores found!")
        return
    
    # Basic descriptive statistics
    pnerd_scores = valid_scores["pnerd_score"]
    
    print(f"\nBasic Statistics:")
    print(f"  Mean: {pnerd_scores.mean():.3f}")
    print(f"  Median: {pnerd_scores.median():.3f}")
    print(f"  Standard Deviation: {pnerd_scores.std():.3f}")
    print(f"  Minimum: {pnerd_scores.min():.3f}")
    print(f"  Maximum: {pnerd_scores.max():.3f}")
    print(f"  Range: {pnerd_scores.max() - pnerd_scores.min():.3f}")
    
    # Percentiles
    print(f"\nPercentiles:")
    for p in [10, 25, 50, 75, 90, 95, 99]:
        value = pnerd_scores.quantile(p/100)
        print(f"  {p}th percentile: {value:.3f}")
    
    # Distribution by bins
    print(f"\nScore Distribution (by ranges):")
    bins = [-10, 0, 2, 4, 6, 8, 10, 15, 20]
    for i in range(len(bins)-1):
        low, high = bins[i], bins[i+1]
        count = len(pnerd_scores[(pnerd_scores >= low) & (pnerd_scores < high)])
        pct = count / len(pnerd_scores) * 100
        print(f"  {low:.0f} to {high:.0f}: {count} pitchers ({pct:.1f}%)")
    
    # Outliers (beyond 2 standard deviations)
    mean = pnerd_scores.mean()
    std = pnerd_scores.std()
    low_outliers = pnerd_scores[pnerd_scores < (mean - 2*std)]
    high_outliers = pnerd_scores[pnerd_scores > (mean + 2*std)]
    
    print(f"\nOutliers (beyond 2 std devs):")
    print(f"  Low outliers (< {mean - 2*std:.3f}): {len(low_outliers)}")
    print(f"  High outliers (> {mean + 2*std:.3f}): {len(high_outliers)}")
    
    if len(high_outliers) > 0:
        print(f"\nTop performers (high outliers):")
        top_performers = valid_scores[valid_scores["pnerd_score"].isin(high_outliers)]
        for _, row in top_performers.sort_values("pnerd_score", ascending=False).iterrows():
            print(f"  {row['pitcher_name']} ({row['pitcher_team']}): {row['pnerd_score']:.3f}")
    
    if len(low_outliers) > 0:
        print(f"\nLow performers (low outliers):")
        low_performers = valid_scores[valid_scores["pnerd_score"].isin(low_outliers)]
        for _, row in low_performers.sort_values("pnerd_score").iterrows():
            print(f"  {row['pitcher_name']} ({row['pitcher_team']}): {row['pnerd_score']:.3f}")


def analyze_component_contributions(df: pd.DataFrame) -> None:
    """
    Analyze how different components contribute to pNERD scores.
    """
    print("\n" + "="*80)
    print("PNERD COMPONENT ANALYSIS")
    print("="*80)
    
    # Filter out rows with missing pNERD scores
    valid_scores = df.dropna(subset=["pnerd_score"])
    
    if len(valid_scores) == 0:
        print("\nNo valid pNERD scores found!")
        return
    
    components = [
        "xfip_component", "swinging_strike_component", "strike_component",
        "velocity_component", "age_component", "pace_component", 
        "luck_component", "knuckleball_component", "constant_component"
    ]
    
    print(f"\nComponent Statistics (mean ± std):")
    for component in components:
        if component in valid_scores.columns:
            values = valid_scores[component].dropna()
            if len(values) > 0:
                mean_val = values.mean()
                std_val = values.std()
                print(f"  {component:25}: {mean_val:6.3f} ± {std_val:5.3f}")
    
    # Correlation with total pNERD score
    print(f"\nCorrelation with total pNERD score:")
    for component in components:
        if component in valid_scores.columns:
            corr = valid_scores["pnerd_score"].corr(valid_scores[component])
            if not pd.isna(corr):
                print(f"  {component:25}: {corr:6.3f}")


def main():
    """Main analysis function."""
    print("MLB pNERD Score Analysis - Last Seven Days")
    print("=" * 50)
    
    # Get the last seven days
    dates = get_last_seven_days()
    print(f"Analyzing dates: {', '.join(dates)}")
    
    # Collect games and pitchers
    print("\nCollecting game and pitcher data...")
    game_pitcher_data = collect_games_and_pitchers(dates)
    
    if not game_pitcher_data:
        print("No game data found for the specified dates!")
        return
    
    print(f"Found {len(game_pitcher_data)} game/pitcher combinations")
    
    # Add pNERD scores
    df = add_pnerd_scores(game_pitcher_data)
    
    # Save raw data to CSV
    output_file = "analysis/pnerd_analysis_raw_data.csv"
    df.to_csv(output_file, index=False)
    print(f"\nRaw data saved to: {output_file}")
    
    # Perform analysis
    analyze_pnerd_distribution(df)
    analyze_component_contributions(df)
    
    print(f"\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()