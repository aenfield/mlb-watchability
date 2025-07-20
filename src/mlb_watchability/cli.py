"""Command-line interface for MLB Watchability."""

from datetime import datetime, timedelta
from typing import Any

import typer

from mlb_watchability.data_retrieval import get_game_schedule
from mlb_watchability.game_scores import GameScore, calculate_game_scores
from mlb_watchability.pitcher_stats import (
    calculate_detailed_pitcher_nerd_scores,
)
from mlb_watchability.team_mappings import get_team_abbreviation
from mlb_watchability.team_stats import (
    calculate_detailed_team_nerd_scores,
)

app = typer.Typer()


def get_today() -> str:
    """Get today's date."""
    today = datetime.now()
    return today.strftime("%Y-%m-%d")


def get_tomorrow() -> str:
    """Get tomorrow's date."""
    tomorrow = datetime.now() + timedelta(days=1)
    return tomorrow.strftime("%Y-%m-%d")


def extract_year_from_date(date_str: str) -> int:
    """Extract year from a date string in YYYY-MM-DD format."""
    try:
        return int(date_str.split("-")[0])
    except (ValueError, IndexError):
        # Default to current year if parsing fails
        return datetime.now().year


def format_team_nerd_breakdown(team_nerd_details: dict[str, Any]) -> str:
    """Format detailed team NERD breakdown for display."""
    if not team_nerd_details:
        return "No team NERD data available"

    lines = ["Team NERD Score Breakdown:"]
    lines.append("=" * 120)

    # Header
    header = f"{'Team':<4} {'tNERD':<6} {'Bat':<5} {'zBat':<6} {'Barrel%':<7} {'zBarrel':<8} {'BsR':<5} {'zBsR':<6} {'Fld':<5} {'zFld':<6} {'Pay':<5} {'zPay':<6} {'Age':<5} {'zAge':<6} {'Luck':<5} {'zLuck':<6}"
    lines.append(header)
    lines.append("-" * 120)

    # Sort teams by tNERD score (highest first)
    sorted_teams = sorted(
        team_nerd_details.items(), key=lambda x: x[1].tnerd_score, reverse=True
    )

    for team_abbr, team_nerd_stats in sorted_teams:
        team_stats = team_nerd_stats.team_stats
        line = (
            f"{team_abbr:<4} "
            f"{team_nerd_stats.tnerd_score:<6.1f} "
            f"{team_stats.batting_runs:<5.0f} "
            f"{team_nerd_stats.z_batting_runs:<6.2f} "
            f"{team_stats.barrel_rate:<7.3f} "
            f"{team_nerd_stats.z_barrel_rate:<8.2f} "
            f"{team_stats.baserunning_runs:<5.0f} "
            f"{team_nerd_stats.z_baserunning_runs:<6.2f} "
            f"{team_stats.fielding_runs:<5.0f} "
            f"{team_nerd_stats.z_fielding_runs:<6.2f} "
            f"{team_stats.payroll:<5.0f} "
            f"{team_nerd_stats.adjusted_payroll:<6.2f} "
            f"{team_stats.age:<5.1f} "
            f"{team_nerd_stats.adjusted_age:<6.2f} "
            f"{team_stats.luck:<5.0f} "
            f"{team_nerd_stats.adjusted_luck:<6.2f}"
        )
        lines.append(line)

    return "\n".join(lines)


def format_pitcher_nerd_breakdown(
    pitcher_nerd_details: dict[str, Any], games: list[dict[str, Any]] | None = None
) -> str:
    """Format detailed pitcher NERD breakdown for display."""
    if not pitcher_nerd_details:
        return "No pitcher NERD data available"

    # Filter pitchers to only those in today's games if games are provided
    filtered_pitcher_details = pitcher_nerd_details
    if games:
        todays_pitchers = set()
        for game in games:
            away_starter = game.get("away_starter")
            home_starter = game.get("home_starter")
            if away_starter and away_starter != "TBD":
                todays_pitchers.add(away_starter)
            if home_starter and home_starter != "TBD":
                todays_pitchers.add(home_starter)

        filtered_pitcher_details = {
            name: stats
            for name, stats in pitcher_nerd_details.items()
            if name in todays_pitchers
        }

    if not filtered_pitcher_details:
        return "No pitcher NERD data available for today's games"

    lines = ["Pitcher NERD Score Breakdown (Today's Starting Pitchers):"]
    lines.append("=" * 140)

    # Header
    header = f"{'Pitcher':<20} {'pNERD':<6} {'xFIP-':<6} {'zxFIP':<7} {'SwStr%':<6} {'zSwStr':<7} {'Str%':<5} {'zStr':<6} {'Velo':<5} {'zVelo':<6} {'Age':<4} {'zAge':<6} {'Pace':<5} {'zPace':<6} {'Luck':<5} {'KN%':<4}"
    lines.append(header)
    lines.append("-" * 140)

    # Sort pitchers by pNERD score (highest first)
    sorted_pitchers = sorted(
        filtered_pitcher_details.items(), key=lambda x: x[1].pnerd_score, reverse=True
    )

    for pitcher_name, pitcher_nerd_stats in sorted_pitchers:
        pitcher_stats = pitcher_nerd_stats.pitcher_stats
        line = (
            f"{pitcher_name:<20} "
            f"{pitcher_nerd_stats.pnerd_score:<6.1f} "
            f"{pitcher_stats.xfip_minus:<6.0f} "
            f"{pitcher_nerd_stats.z_xfip_minus:<7.2f} "
            f"{pitcher_stats.swinging_strike_rate:<6.3f} "
            f"{pitcher_nerd_stats.z_swinging_strike_rate:<7.2f} "
            f"{pitcher_stats.strike_rate:<5.3f} "
            f"{pitcher_nerd_stats.z_strike_rate:<6.2f} "
            f"{pitcher_stats.velocity:<5.1f} "
            f"{pitcher_nerd_stats.adjusted_velocity:<6.2f} "
            f"{pitcher_stats.age:<4} "
            f"{pitcher_nerd_stats.adjusted_age:<6.2f} "
            f"{pitcher_stats.pace:<5.1f} "
            f"{pitcher_nerd_stats.z_pace:<6.2f} "
            f"{pitcher_stats.luck:<5.0f} "
            f"{pitcher_stats.knuckleball_rate:<4.3f}"
        )
        lines.append(line)

    return "\n".join(lines)


def format_games_output(
    games: list[dict[str, Any]],
    date: str,
    team_nerd_scores: dict[str, float] | None = None,
    pitcher_nerd_scores: dict[str, float] | None = None,
) -> str:
    """Format games list for display."""
    if not games:
        return f"No games found for {date}"

    lines = [f"Games for {date}:"]
    for game in games:
        away_starter = game["away_starter"] or "TBD"
        home_starter = game["home_starter"] or "TBD"
        game_time = game["time"] or "TBD"

        # Format team names with NERD scores if available
        if team_nerd_scores:
            away_abbr = get_team_abbreviation(game["away_team"])
            home_abbr = get_team_abbreviation(game["home_team"])

            away_nerd = team_nerd_scores.get(away_abbr, 0.0)
            home_nerd = team_nerd_scores.get(home_abbr, 0.0)

            away_team_display = f"{game['away_team']} ({away_nerd:.1f})"
            home_team_display = f"{game['home_team']} ({home_nerd:.1f})"
        else:
            away_team_display = game["away_team"]
            home_team_display = game["home_team"]

        # Format pitcher names with NERD scores if available
        if pitcher_nerd_scores and away_starter != "TBD":
            away_pitcher_nerd = pitcher_nerd_scores.get(away_starter)
            if away_pitcher_nerd is not None:
                away_pitcher_display = f"{away_starter} ({away_pitcher_nerd:.1f})"
            else:
                away_pitcher_display = away_starter
        else:
            away_pitcher_display = away_starter

        if pitcher_nerd_scores and home_starter != "TBD":
            home_pitcher_nerd = pitcher_nerd_scores.get(home_starter)
            if home_pitcher_nerd is not None:
                home_pitcher_display = f"{home_starter} ({home_pitcher_nerd:.1f})"
            else:
                home_pitcher_display = home_starter
        else:
            home_pitcher_display = home_starter

        game_info = f"  {game_time} - {away_team_display} @ {home_team_display} - {away_pitcher_display} vs {home_pitcher_display}"
        lines.append(game_info)

    return "\n".join(lines)


def format_games_with_gnerd_scores(game_scores: list[GameScore], date: str) -> str:
    """Format games list with gNERD scores for display, ordered by score."""
    if not game_scores:
        return f"No games found for {date}"

    lines = [f"Games for {date} (ordered by gNERD score):"]
    lines.append("=" * 100)

    for i, game_score in enumerate(game_scores, 1):
        away_starter = game_score.away_starter or "TBD"
        home_starter = game_score.home_starter or "TBD"
        game_time = game_score.game_time or "TBD"

        # Format team names with individual tNERD scores
        away_team_display = (
            f"{game_score.away_team} (tNERD: {game_score.away_team_nerd:.1f})"
        )
        home_team_display = (
            f"{game_score.home_team} (tNERD: {game_score.home_team_nerd:.1f})"
        )

        # Format pitcher names with individual pNERD scores
        if game_score.away_pitcher_nerd is not None:
            away_pitcher_display = (
                f"{away_starter} (pNERD: {game_score.away_pitcher_nerd:.1f})"
            )
        else:
            away_pitcher_display = away_starter

        if game_score.home_pitcher_nerd is not None:
            home_pitcher_display = (
                f"{home_starter} (pNERD: {game_score.home_pitcher_nerd:.1f})"
            )
        else:
            home_pitcher_display = home_starter

        # Game info with gNERD score prominently displayed
        game_info = (
            f"{i:2d}. gNERD: {game_score.gnerd_score:.1f} - {game_time} - "
            f"{away_team_display} @ {home_team_display}\n"
            f"     {away_pitcher_display} vs {home_pitcher_display}"
        )
        lines.append(game_info)
        lines.append("")  # Empty line between games

    return "\n".join(lines)


@app.command()
def main(
    date: str | None = typer.Argument(
        default=None,
        help="Date to calculate game scores for (YYYY-MM-DD format). Defaults to today and tomorrow.",
    ),
) -> None:
    """Calculate Game NERD scores for MLB games on a given date."""
    if date is not None:
        # Show games for specific date with gNERD scores
        try:
            games = get_game_schedule(date)
            season = extract_year_from_date(date)
            game_scores = calculate_game_scores(games, season)
            typer.echo(format_games_with_gnerd_scores(game_scores, date))
        except Exception as e:
            typer.echo(f"Error retrieving games for {date}: {e}", err=True)
    else:
        # Show games for today and tomorrow
        today = get_today()
        tomorrow = get_tomorrow()

        typer.echo("MLB Watchability - Game Schedule")
        typer.echo("=" * 40)

        # Calculate season for today
        today_season = extract_year_from_date(today)

        # Calculate detailed breakdowns
        team_nerd_details = calculate_detailed_team_nerd_scores(today_season)
        pitcher_nerd_details = calculate_detailed_pitcher_nerd_scores(today_season)

        # Today's games with gNERD scores
        today_games = []
        try:
            today_games = get_game_schedule(today)
            game_scores = calculate_game_scores(today_games, today_season)
            typer.echo(format_games_with_gnerd_scores(game_scores, f"Today ({today})"))
        except Exception as e:
            typer.echo(f"Error retrieving games for today: {e}", err=True)

        typer.echo("")
        typer.echo("")

        # Team NERD breakdown
        typer.echo(format_team_nerd_breakdown(team_nerd_details))

        typer.echo("")
        typer.echo("")

        # Pitcher NERD breakdown (filtered to today's pitchers)
        typer.echo(format_pitcher_nerd_breakdown(pitcher_nerd_details, today_games))

        typer.echo("")
        typer.echo("")

        # Tomorrow's games (without NERD scores since we can't predict pitchers)
        try:
            tomorrow_games = get_game_schedule(tomorrow)
            typer.echo(format_games_output(tomorrow_games, f"Tomorrow ({tomorrow})"))
        except Exception as e:
            typer.echo(f"Error retrieving games for tomorrow: {e}", err=True)


if __name__ == "__main__":
    app()
