#!/usr/bin/env python3
"""
Historical NERD Score Analysis

Analyzes historical gNERD, tNERD, and pNERD scores from generated markdown files
to understand score distributions and calculate summary statistics.
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from datetime import datetime
import sys
import os
from typing import List, Dict, Any

# Add src to path to import project modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mlb_watchability.team_mappings import get_team_abbreviation


def extract_team_name_from_link(markdown_link: str) -> str:
    """Extract team name from markdown link format [Team Name](url)."""
    match = re.match(r"\[([^\]]+)\]", markdown_link.strip())
    return match.group(1) if match else markdown_link.strip()


def extract_pitcher_name_from_link(markdown_link: str) -> str:
    """Extract pitcher name from markdown link format [Pitcher Name](url)."""
    match = re.match(r"\[([^\]]+)\]", markdown_link.strip())
    return match.group(1) if match else markdown_link.strip()


def parse_score_value(score_str: str) -> float:
    """Parse score value, handling 'No data' cases and markdown links."""
    score_str = score_str.strip()
    if score_str.lower() in ["no data", ""]:
        return np.nan

    # Handle markdown links like [14.9](#...)
    link_match = re.match(r"\[([^\]]+)\]", score_str)
    if link_match:
        score_str = link_match.group(1)

    try:
        return float(score_str)
    except ValueError:
        return np.nan


def extract_date_from_filename(filename: str) -> str:
    """Extract date from filename like mlb_what_to_watch_2025_07_29.md."""
    match = re.search(r"(\d{4}_\d{2}_\d{2})", filename)
    if match:
        return match.group(1).replace("_", "-")
    return ""


def parse_markdown_file(file_path: Path) -> List[Dict[str, Any]]:
    """Parse a single markdown file and extract game data."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract date from filename
        date_str = extract_date_from_filename(file_path.name)

        # Find the main table (between {% wideTable %} tags)
        table_match = re.search(
            r"{% wideTable %}.*?\n(.*?){% endwideTable %}", content, re.DOTALL
        )
        if not table_match:
            print(f"Warning: No table found in {file_path.name}")
            return []

        table_content = table_match.group(1)

        # Split into lines and filter out header and separator rows
        lines = [line.strip() for line in table_content.split("\n") if line.strip()]

        # Skip header row (starts with | Score |) and separator row (starts with |-----)
        data_rows = [
            line
            for line in lines
            if not line.startswith("| Score |") and not line.startswith("|-------")
        ]

        games = []
        for line in data_rows:
            if not line.startswith("|") or not line.endswith("|"):
                continue

            # Split by | and clean up
            parts = [
                part.strip() for part in line.split("|")[1:-1]
            ]  # Remove first and last empty parts

            if len(parts) != 10:
                print(f"Warning: Unexpected row format in {file_path.name}: {line}")
                continue

            try:
                # Extract data from table columns
                gnerd_score = parse_score_value(parts[0])
                visiting_team = extract_team_name_from_link(parts[2])
                visiting_tnerd = parse_score_value(parts[3])
                home_team = extract_team_name_from_link(parts[4])
                home_tnerd = parse_score_value(parts[5])
                visiting_pitcher = extract_pitcher_name_from_link(parts[6])
                visiting_pnerd = parse_score_value(parts[7])
                home_pitcher = extract_pitcher_name_from_link(parts[8])
                home_pnerd = parse_score_value(parts[9])

                # Convert team names to abbreviations
                visiting_abbrev = get_team_abbreviation(visiting_team)
                home_abbrev = get_team_abbreviation(home_team)

                game_data = {
                    "date": date_str,
                    "gnerd_score": gnerd_score,
                    "visiting_tnerd": visiting_tnerd,
                    "home_tnerd": home_tnerd,
                    "visiting_pnerd": visiting_pnerd,
                    "home_pnerd": home_pnerd,
                    "visiting_team": visiting_abbrev,
                    "home_team": home_abbrev,
                    "visiting_pitcher": visiting_pitcher,
                    "home_pitcher": home_pitcher,
                }

                games.append(game_data)

            except Exception as e:
                print(f"Warning: Error parsing row in {file_path.name}: {line}")
                print(f"Error: {e}")
                continue

        return games

    except Exception as e:
        print(f"Error reading {file_path.name}: {e}")
        return []


def analyze_historical_scores() -> None:
    """Main function to analyze historical NERD scores."""
    # Get markdown files directory (sibling to mlb-watchability)
    blog_dir = (
        Path(__file__).parent.parent.parent
        / "blog-eleventy"
        / "content"
        / "blog"
        / "mlbw"
    )

    if not blog_dir.exists():
        print(f"Error: Blog directory not found at {blog_dir}")
        return

    # Find all markdown files (excluding special files)
    md_files = [f for f in blog_dir.glob("mlb_what_to_watch_*.md") if f.is_file()]

    if not md_files:
        print(f"Error: No markdown files found in {blog_dir}")
        return

    print(f"Found {len(md_files)} markdown files to process")

    # Parse all files
    all_games = []
    for md_file in sorted(md_files):
        games = parse_markdown_file(md_file)
        print(f"Processing {md_file.name}... found {len(games)} games")
        all_games.extend(games)

    if not all_games:
        print("Error: No game data extracted from files")
        return

    # Create DataFrame
    df = pd.DataFrame(all_games)

    print(f"\nProcessed {len(df)} games from {len(md_files)} files")

    # Save to CSV
    output_dir = Path(__file__).parent
    csv_path = output_dir / "historical_nerd_scores.csv"

    # Save with empty strings for NaN values to get ,, in CSV
    df.to_csv(csv_path, index=False, na_rep="")
    print(f"Saved data to {csv_path}")

    # Calculate and print summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)

    # gNERD scores
    gnerd_scores = df["gnerd_score"].dropna()
    gnerd_nulls = df["gnerd_score"].isna().sum()
    print(f"\ngNERD Scores (n={len(gnerd_scores)}, nulls={gnerd_nulls}):")
    print(f"  Mean: {gnerd_scores.mean():.2f}")

    # Find min and max with context
    min_idx = gnerd_scores.idxmin()
    max_idx = gnerd_scores.idxmax()
    min_row = df.loc[min_idx]
    max_row = df.loc[max_idx]

    print(
        f"  Min:  {gnerd_scores.min():.2f} ({min_row['date']}: {min_row['visiting_team']} @ {min_row['home_team']})"
    )
    print(
        f"  Max:  {gnerd_scores.max():.2f} ({max_row['date']}: {max_row['visiting_team']} @ {max_row['home_team']})"
    )
    print(f"  Percentiles:")
    print(f"    5%:   {gnerd_scores.quantile(0.05):.2f}")
    print(f"    25%:  {gnerd_scores.quantile(0.25):.2f}")
    print(f"    50%:  {gnerd_scores.quantile(0.50):.2f}")
    print(f"    75%:  {gnerd_scores.quantile(0.75):.2f}")
    print(f"    95%:  {gnerd_scores.quantile(0.95):.2f}")

    # tNERD scores (combine visiting and home)
    visiting_tnerd = df["visiting_tnerd"].copy()
    home_tnerd = df["home_tnerd"].copy()

    # Add team names for context
    visiting_tnerd_with_team = pd.DataFrame(
        {"score": visiting_tnerd, "team": df["visiting_team"], "date": df["date"]}
    )
    home_tnerd_with_team = pd.DataFrame(
        {"score": home_tnerd, "team": df["home_team"], "date": df["date"]}
    )

    tnerd_combined = pd.concat([visiting_tnerd_with_team, home_tnerd_with_team])
    tnerd_scores = tnerd_combined["score"].dropna()
    tnerd_nulls = tnerd_combined["score"].isna().sum()

    print(f"\ntNERD Scores (n={len(tnerd_scores)}, nulls={tnerd_nulls}):")
    print(f"  Mean: {tnerd_scores.mean():.2f}")

    # Find min and max with context
    tnerd_no_nulls = tnerd_combined.dropna(subset=["score"]).reset_index(drop=True)
    min_idx = tnerd_no_nulls["score"].idxmin()
    max_idx = tnerd_no_nulls["score"].idxmax()
    min_row = tnerd_no_nulls.loc[min_idx]
    max_row = tnerd_no_nulls.loc[max_idx]

    print(f"  Min:  {tnerd_scores.min():.2f} ({min_row['date']}: {min_row['team']})")
    print(f"  Max:  {tnerd_scores.max():.2f} ({max_row['date']}: {max_row['team']})")
    print(f"  Percentiles:")
    print(f"    5%:   {tnerd_scores.quantile(0.05):.2f}")
    print(f"    25%:  {tnerd_scores.quantile(0.25):.2f}")
    print(f"    50%:  {tnerd_scores.quantile(0.50):.2f}")
    print(f"    75%:  {tnerd_scores.quantile(0.75):.2f}")
    print(f"    95%:  {tnerd_scores.quantile(0.95):.2f}")

    # pNERD scores (combine visiting and home)
    visiting_pnerd = df["visiting_pnerd"].copy()
    home_pnerd = df["home_pnerd"].copy()

    # Add pitcher names for context
    visiting_pnerd_with_pitcher = pd.DataFrame(
        {"score": visiting_pnerd, "pitcher": df["visiting_pitcher"], "date": df["date"]}
    )
    home_pnerd_with_pitcher = pd.DataFrame(
        {"score": home_pnerd, "pitcher": df["home_pitcher"], "date": df["date"]}
    )

    pnerd_combined = pd.concat([visiting_pnerd_with_pitcher, home_pnerd_with_pitcher])
    pnerd_scores = pnerd_combined["score"].dropna()
    pnerd_nulls = pnerd_combined["score"].isna().sum()

    print(f"\npNERD Scores (n={len(pnerd_scores)}, nulls={pnerd_nulls}):")
    print(f"  Mean: {pnerd_scores.mean():.2f}")

    # Find min and max with context
    pnerd_no_nulls = pnerd_combined.dropna(subset=["score"]).reset_index(drop=True)
    min_idx = pnerd_no_nulls["score"].idxmin()
    max_idx = pnerd_no_nulls["score"].idxmax()
    min_row = pnerd_no_nulls.loc[min_idx]
    max_row = pnerd_no_nulls.loc[max_idx]

    print(f"  Min:  {pnerd_scores.min():.2f} ({min_row['date']}: {min_row['pitcher']})")
    print(f"  Max:  {pnerd_scores.max():.2f} ({max_row['date']}: {max_row['pitcher']})")
    print(f"  Percentiles:")
    print(f"    5%:   {pnerd_scores.quantile(0.05):.2f}")
    print(f"    25%:  {pnerd_scores.quantile(0.25):.2f}")
    print(f"    50%:  {pnerd_scores.quantile(0.50):.2f}")
    print(f"    75%:  {pnerd_scores.quantile(0.75):.2f}")
    print(f"    95%:  {pnerd_scores.quantile(0.95):.2f}")

    print(f"\nData saved to: {csv_path}")


if __name__ == "__main__":
    analyze_historical_scores()
