"""Markdown file generation for MLB Watchability."""

from datetime import datetime

from .game_scores import GameScore
from .pitcher_stats import format_pitcher_with_fangraphs_link
from .team_mappings import format_team_with_fangraphs_link
from .utils import format_time_12_hour

# Template configuration - easily modifiable
METADATA_TEMPLATE = """---
title: "MLB: What to watch on {formatted_date}"
date: {iso_date}
tags: mlbw
---"""

INTRO_TEXT = """Here are today's MLB games, ordered by watchability, based on how interesting the teams and starting pitchers look. Higher is better.

This is inspired by [Carson Cistulli's NERD scores](https://blogs.fangraphs.com/introducing-team-nerd/) at FanGraphs. (I'll write a bit about the details of [my implementation on GitHub](https://github.com/aenfield/mlb-watchability) soon, and then link to that from this intro.)
"""

FOOTER_TEXT = """Notes:

- **Pitcher 'no data'**: Pitchers only have a pNERD score once they've started at least one game and have at least 20 innings pitched. I might also show 'no data' when I'm not correctly linking the schedule information with a pitcher's stats, like if the names don't match (I have an open issue to improve this).
"""

TABLE_HEADER = "| Score | Time (EDT) | Visitors | Score | Home | Score | Starter (V) | Score | Starter (H) | Score |"
TABLE_SEPARATOR = "|-------|------------|----------|-------|------|-------|-------------|-------|-------------|-------|"


def generate_metadata_block(date_str: str) -> str:
    """
    Generate the YAML metadata block for the markdown file.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Formatted metadata block with title, date, and tags
    """
    # Parse date to get formatted version for title
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")
    except ValueError:
        # Fallback to original string if parsing fails
        formatted_date = date_str

    return METADATA_TEMPLATE.format(formatted_date=formatted_date, iso_date=date_str)


def generate_markdown_table(game_scores: list[GameScore]) -> str:
    """
    Generate a markdown table with game scores and team/pitcher information.

    Args:
        game_scores: List of GameScore objects, should be sorted by gNERD score descending

    Returns:
        Formatted markdown table as string
    """
    if not game_scores:
        return "No games available for table."

    lines = ["{% wideTable %}", "", TABLE_HEADER, TABLE_SEPARATOR]

    for game_score in game_scores:
        # Format time with EDT specification
        time_str = format_time_12_hour(game_score.game_time)

        # Format team names with Fangraphs links
        visitors_team = format_team_with_fangraphs_link(game_score.away_team)
        home_team = format_team_with_fangraphs_link(game_score.home_team)

        # Format pitcher names with Fangraphs links
        away_pitcher = (
            format_pitcher_with_fangraphs_link(game_score.away_starter)
            if game_score.away_starter
            else "TBD"
        )
        home_pitcher = (
            format_pitcher_with_fangraphs_link(game_score.home_starter)
            if game_score.home_starter
            else "TBD"
        )

        # Format scores
        away_team_score = f"{game_score.away_team_nerd:.1f}"
        home_team_score = f"{game_score.home_team_nerd:.1f}"
        away_pitcher_score = (
            f"{game_score.away_pitcher_nerd:.1f}"
            if game_score.away_pitcher_nerd is not None
            else "No data"
        )
        home_pitcher_score = (
            f"{game_score.home_pitcher_nerd:.1f}"
            if game_score.home_pitcher_nerd is not None
            else "No data"
        )

        # Add table row
        row = f"| {game_score.gnerd_score:.1f} | {time_str} | {visitors_team} | {away_team_score} | {home_team} | {home_team_score} | {away_pitcher} | {away_pitcher_score} | {home_pitcher} | {home_pitcher_score} |"
        lines.append(row)

    lines.append("{% endwideTable %}")
    return "\n".join(lines)


def generate_complete_markdown_content(
    date_str: str, game_scores: list[GameScore]
) -> str:
    """
    Generate the complete markdown file content.

    Args:
        date_str: Date string in YYYY-MM-DD format
        game_scores: List of GameScore objects, should be sorted by gNERD score descending

    Returns:
        Complete markdown file content as string
    """
    metadata_block = generate_metadata_block(date_str)
    table_content = generate_markdown_table(game_scores)

    # Combine all parts with proper spacing
    content_parts = [
        metadata_block,
        "",  # Empty line after metadata
        INTRO_TEXT,
        "",  # Empty line before table
        table_content,
        "",  # Empty line after table
        FOOTER_TEXT,
        "",  # Final newline
    ]

    return "\n".join(content_parts)


def generate_markdown_filename(date_str: str) -> str:
    """
    Generate the markdown filename based on the date.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Filename in format mlb_what_to_watch_2025_07_20.md
    """
    # Replace dashes with underscores for filename
    date_underscore = date_str.replace("-", "_")
    return f"mlb_what_to_watch_{date_underscore}.md"
