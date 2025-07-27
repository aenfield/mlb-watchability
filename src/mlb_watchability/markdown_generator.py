"""Markdown file generation for MLB Watchability."""

import re
import unicodedata
from datetime import datetime

from .game_scores import GameScore
from .pitcher_stats import (
    PitcherNerdStats,
    find_pitcher_nerd_stats_fuzzy,
    format_pitcher_with_fangraphs_link,
)
from .team_mappings import format_team_with_fangraphs_link, get_team_abbreviation
from .team_stats import TeamNerdStats
from .utils import format_time_12_hour


def generate_automatic_anchor_id(heading_text: str) -> str:
    """
    Generate an anchor ID that matches the automatic anchor generation from heading text.

    This follows the pattern used by 11ty and other markdown processors:
    - Normalize accented characters to ASCII equivalents (ú → u, é → e)
    - Convert to lowercase
    - Replace spaces and special characters with hyphens
    - Remove multiple consecutive hyphens
    - Remove leading/trailing hyphens

    I had Claude research canned alternatives to this custom code and it came up with
    @sindresorhus/slugify and github-slugger. For now, I'll keep this impl since it's
    simple and works and avoids a dependency, but can revisit in the future.

    Args:
        heading_text: The heading text (without ## or ### prefixes)

    Returns:
        URL-safe anchor ID that matches automatic generation
    """
    # Handle special character mappings that NFD doesn't decompose
    char_map = {
        "æ": "ae",
        "œ": "oe",
        "ß": "ss",
        "ð": "d",
        "þ": "th",
        "ø": "o",
        "Æ": "AE",
        "Œ": "OE",
        "Ð": "D",
        "Þ": "TH",
        "Ø": "O",
    }

    # Apply character mappings
    text = heading_text
    for char, replacement in char_map.items():
        text = text.replace(char, replacement)

    # Normalize accented characters to ASCII equivalents
    # NFD normalization decomposes characters, then we filter out combining marks
    normalized = unicodedata.normalize("NFD", text)
    ascii_text = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )

    # Convert to lowercase and replace spaces and special characters with hyphens
    anchor_id = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text)
    # Remove multiple consecutive hyphens
    anchor_id = re.sub(r"-+", "-", anchor_id)
    # Remove leading/trailing hyphens
    anchor_id = anchor_id.strip("-").lower()
    return anchor_id


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

        # Generate automatic anchor IDs based on heading text
        # Game heading: "## Away Team @ Home Team, 3:40p"
        game_heading = f"{game_score.away_team} @ {game_score.home_team}, {time_str}"
        game_anchor_id = generate_automatic_anchor_id(game_heading)

        # Team headings: "### Team Name"
        away_team_anchor_id = generate_automatic_anchor_id(game_score.away_team)
        home_team_anchor_id = generate_automatic_anchor_id(game_score.home_team)

        # Format scores with anchor links
        game_score_link = f"[{game_score.gnerd_score:.1f}](#{game_anchor_id})"
        away_team_score_link = (
            f"[{game_score.away_team_nerd:.1f}](#{away_team_anchor_id})"
        )
        home_team_score_link = (
            f"[{game_score.home_team_nerd:.1f}](#{home_team_anchor_id})"
        )

        # Format pitcher scores with anchor links
        if game_score.away_pitcher_nerd is not None and game_score.away_starter:
            # Pitcher heading: "### Visiting starter: Pitcher Name"
            away_pitcher_heading = f"Visiting starter: {game_score.away_starter}"
            away_pitcher_anchor_id = generate_automatic_anchor_id(away_pitcher_heading)
            away_pitcher_score = (
                f"[{game_score.away_pitcher_nerd:.1f}](#{away_pitcher_anchor_id})"
            )
        else:
            away_pitcher_score = "No data"

        if game_score.home_pitcher_nerd is not None and game_score.home_starter:
            # Pitcher heading: "### Home starter: Pitcher Name"
            home_pitcher_heading = f"Home starter: {game_score.home_starter}"
            home_pitcher_anchor_id = generate_automatic_anchor_id(home_pitcher_heading)
            home_pitcher_score = (
                f"[{game_score.home_pitcher_nerd:.1f}](#{home_pitcher_anchor_id})"
            )
        else:
            home_pitcher_score = "No data"

        # Add table row
        row = f"| {game_score_link} | {time_str} | {visitors_team} | {away_team_score_link} | {home_team} | {home_team_score_link} | {away_pitcher} | {away_pitcher_score} | {home_pitcher} | {home_pitcher_score} |"
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
    detail_content = generate_all_game_details(game_scores)

    # Combine all parts with proper spacing
    content_parts = [
        metadata_block,
        "",  # Empty line after metadata
        INTRO_TEXT,
        "",  # Empty line before table
        table_content,
        "",  # Empty line after table
        FOOTER_TEXT,
        "",  # Empty line after footer
        detail_content,
        "",  # Final newline
    ]

    return "\n".join(content_parts)


def generate_team_breakdown_table(
    team_name: str,
    team_nerd_stats: TeamNerdStats,
    team_abbreviation: str,  # noqa: ARG001
) -> str:
    """
    Generate detailed breakdown table for a team.

    Args:
        team_name: Full team name
        team_nerd_stats: TeamNerdStats object
        team_abbreviation: Team abbreviation

    Returns:
        Formatted markdown table showing raw stats, z-scores, and tNERD components
    """
    team_stats = team_nerd_stats.team_stats

    # Format payroll as millions with M suffix
    payroll_str = f"${team_stats.payroll:.1f}M"

    # Create table rows
    raw_row = (
        f"| **Raw Stat** "
        f"| {team_stats.batting_runs:.1f} "
        f"| {team_stats.barrel_rate:.1%} "
        f"| {team_stats.baserunning_runs:.1f} "
        f"| {team_stats.fielding_runs:.1f} "
        f"| {payroll_str} "
        f"| {team_stats.age:.1f} "
        f"| {team_stats.luck:.1f} "
        f"| — "
        f"| — |"
    )

    z_row = (
        f"| **Z-Score** "
        f"| {team_nerd_stats.z_batting_runs:.2f} "
        f"| {team_nerd_stats.z_barrel_rate:.2f} "
        f"| {team_nerd_stats.z_baserunning_runs:.2f} "
        f"| {team_nerd_stats.z_fielding_runs:.2f} "
        f"| {team_nerd_stats.z_payroll:.2f} "
        f"| {team_nerd_stats.z_age:.2f} "
        f"| {team_nerd_stats.z_luck:.2f} "
        f"| — "
        f"| — |"
    )

    tnerd_row = (
        f"| **tNERD** "
        f"| {team_nerd_stats.batting_component:.2f} "
        f"| {team_nerd_stats.barrel_component:.2f} "
        f"| {team_nerd_stats.baserunning_component:.2f} "
        f"| {team_nerd_stats.fielding_component:.2f} "
        f"| {team_nerd_stats.payroll_component:.2f} "
        f"| {team_nerd_stats.age_component:.2f} "
        f"| {team_nerd_stats.luck_component:.2f} "
        f"| {team_nerd_stats.constant_component:.2f} "
        f"| {team_nerd_stats.tnerd_score:.2f} |"
    )

    lines = [
        f"### {team_name}",
        "",
        "{% wideTable %}",
        "",
        "|              | Batting Runs | Barrel % | Baserunning | Fielding | Payroll | Age   | Luck | Constant | TOTAL |",
        "| ------------ | ------------ | -------- | ----------- | -------- | ------- | ----- | ---- | -------- | ----- |",
        raw_row,
        z_row,
        tnerd_row,
        "{% endwideTable %}",
        "",
    ]

    return "\n".join(lines)


def generate_pitcher_breakdown_table(
    pitcher_name: str,
    pitcher_nerd_stats: PitcherNerdStats,
    is_home: bool = False,
) -> str:
    """
    Generate detailed breakdown table for a pitcher.

    Args:
        pitcher_name: Pitcher name
        pitcher_nerd_stats: PitcherNerdStats object
        is_home: Whether this is the home team pitcher

    Returns:
        Formatted markdown table showing raw stats, z-scores, and pNERD components
    """
    pitcher_stats = pitcher_nerd_stats.pitcher_stats

    starter_type = "Home starter" if is_home else "Visiting starter"

    # Format velocity with mph suffix
    velocity_str = f"{pitcher_stats.velocity:.1f} mph"

    # Format pace with seconds suffix
    pace_str = f"{pitcher_stats.pace:.1f}s"

    # Create table rows
    raw_row = (
        f"| **Raw Stat** "
        f"| {pitcher_stats.xfip_minus:.0f} "
        f"| {pitcher_stats.swinging_strike_rate:.1%} "
        f"| {pitcher_stats.strike_rate:.1%} "
        f"| {velocity_str} "
        f"| {pitcher_stats.age} "
        f"| {pace_str} "
        f"| {pitcher_stats.luck:.0f} "
        f"| {pitcher_stats.knuckleball_rate:.1%} "
        f"| — "
        f"| — |"
    )

    z_row = (
        f"| **Z-Score** "
        f"| {pitcher_nerd_stats.z_xfip_minus:.2f} "
        f"| {pitcher_nerd_stats.z_swinging_strike_rate:.2f} "
        f"| {pitcher_nerd_stats.z_strike_rate:.2f} "
        f"| {pitcher_nerd_stats.z_velocity:.2f} "
        f"| {pitcher_nerd_stats.z_age:.2f} "
        f"| {pitcher_nerd_stats.z_pace:.2f} "
        f"| — "
        f"| — "
        f"| — "
        f"| — |"
    )

    pnerd_row = (
        f"| **pNERD** "
        f"| {pitcher_nerd_stats.xfip_component:.2f} "
        f"| {pitcher_nerd_stats.swinging_strike_component:.2f} "
        f"| {pitcher_nerd_stats.strike_component:.2f} "
        f"| {pitcher_nerd_stats.velocity_component:.2f} "
        f"| {pitcher_nerd_stats.age_component:.2f} "
        f"| {pitcher_nerd_stats.pace_component:.2f} "
        f"| {pitcher_nerd_stats.luck_component:.2f} "
        f"| {pitcher_nerd_stats.knuckleball_component:.2f} "
        f"| {pitcher_nerd_stats.constant_component:.2f} "
        f"| {pitcher_nerd_stats.pnerd_score:.2f} |"
    )

    lines = [
        f"### {starter_type}: {pitcher_name}",
        "",
        "{% wideTable %}",
        "",
        "|              | xFIP- | SwStr% | Strike % | Velocity | Age   | Pace  | Luck | KN%  | Constant | TOTAL |",
        "| ------------ | ----- | ------ | -------- | -------- | ----- | ----- | ---- | ---- | -------- | ----- |",
        raw_row,
        z_row,
        pnerd_row,
        "{% endwideTable %}",
        "",
    ]

    return "\n".join(lines)


def generate_game_detail_section(game_score: GameScore) -> str:
    """
    Generate detailed breakdown section for a single game.

    Args:
        game_score: GameScore object containing game information and detailed stats

    Returns:
        Formatted markdown section with detailed breakdowns for teams and pitchers
    """
    # Format game time
    time_str = format_time_12_hour(game_score.game_time)

    # Get team abbreviations for lookup
    away_abbr = get_team_abbreviation(game_score.away_team)
    home_abbr = get_team_abbreviation(game_score.home_team)

    # Start with section header (automatic anchor will be generated)
    lines = [
        f"## {game_score.away_team} @ {game_score.home_team}, {time_str}",
        "",
    ]

    # Add away team breakdown
    if away_abbr in game_score.team_nerd_details:
        lines.append(
            generate_team_breakdown_table(
                game_score.away_team,
                game_score.team_nerd_details[away_abbr],
                away_abbr,
            )
        )

    # Add home team breakdown
    if home_abbr in game_score.team_nerd_details:
        lines.append(
            generate_team_breakdown_table(
                game_score.home_team,
                game_score.team_nerd_details[home_abbr],
                home_abbr,
            )
        )

    # Add visiting pitcher breakdown
    if game_score.away_starter and game_score.away_starter != "TBD":
        away_pitcher_stats = find_pitcher_nerd_stats_fuzzy(
            game_score.pitcher_nerd_details,
            game_score.away_starter,
        )
        if away_pitcher_stats:
            lines.append(
                generate_pitcher_breakdown_table(
                    game_score.away_starter,
                    away_pitcher_stats,
                    is_home=False,
                )
            )

    # Add home pitcher breakdown
    if game_score.home_starter and game_score.home_starter != "TBD":
        home_pitcher_stats = find_pitcher_nerd_stats_fuzzy(
            game_score.pitcher_nerd_details,
            game_score.home_starter,
        )
        if home_pitcher_stats:
            lines.append(
                generate_pitcher_breakdown_table(
                    game_score.home_starter,
                    home_pitcher_stats,
                    is_home=True,
                )
            )

    # Add "Go back to top of page" link at the bottom of each game section
    lines.extend(["", "[Go back to top of page](#)", ""])

    return "\n".join(lines)


def generate_all_game_details(game_scores: list[GameScore]) -> str:
    """
    Generate detailed breakdown sections for all games.

    Args:
        game_scores: List of GameScore objects with detailed stats already calculated

    Returns:
        Formatted markdown with detailed breakdowns for all games
    """
    if not game_scores:
        return ""

    # Generate detail sections - sort by gNERD score descending (highest first)
    sorted_games = sorted(game_scores, key=lambda x: x.gnerd_score, reverse=True)
    lines = ["# Detail", ""]

    for game_score in sorted_games:
        lines.append(generate_game_detail_section(game_score))

    return "\n".join(lines)


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
