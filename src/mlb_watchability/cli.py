"""Command-line interface for MLB Watchability."""

from datetime import datetime, timedelta
from typing import Any

import typer

from mlb_watchability.data_retrieval import get_game_schedule

app = typer.Typer()


def get_last_sunday() -> str:
    """Get the date of last Sunday."""
    today = datetime.now()
    days_since_sunday = (today.weekday() + 1) % 7
    if days_since_sunday == 0:  # Today is Sunday
        last_sunday = today - timedelta(days=7)
    else:
        last_sunday = today - timedelta(days=days_since_sunday)
    return last_sunday.strftime("%Y-%m-%d")


def get_this_friday() -> str:
    """Get the date of this Friday."""
    FRIDAY = 4
    today = datetime.now()
    days_until_friday = (FRIDAY - today.weekday()) % 7
    if days_until_friday == 0 and today.weekday() != FRIDAY:  # Not Friday
        days_until_friday = 7
    this_friday = today + timedelta(days=days_until_friday)
    return this_friday.strftime("%Y-%m-%d")


def format_games_output(games: list[dict[str, Any]], date: str) -> str:
    """Format games list for display."""
    if not games:
        return f"No games found for {date}"

    lines = [f"Games for {date}:"]
    for game in games:
        away_starter = game["away_starter"] or "TBD"
        home_starter = game["home_starter"] or "TBD"
        lines.append(f"  {game['away_team']} @ {game['home_team']} - {away_starter} vs {home_starter}")

    return "\n".join(lines)


@app.command()
def main(
    date: str | None = typer.Argument(
        default=None,
        help="Date to calculate game scores for (YYYY-MM-DD format). Defaults to last Sunday and this Friday.",
    ),
) -> None:
    """Calculate Game NERD scores for MLB games on a given date."""
    if date is not None:
        # Show games for specific date
        try:
            games = get_game_schedule(date)
            typer.echo(format_games_output(games, date))
        except Exception as e:
            typer.echo(f"Error retrieving games for {date}: {e}", err=True)
    else:
        # Show games for last Sunday and this Friday
        last_sunday = get_last_sunday()
        this_friday = get_this_friday()

        typer.echo("MLB Watchability - Game Schedule")
        typer.echo("=" * 40)

        # Last Sunday games
        try:
            sunday_games = get_game_schedule(last_sunday)
            typer.echo(format_games_output(sunday_games, f"Last Sunday ({last_sunday})"))
        except Exception as e:
            typer.echo(f"Error retrieving games for last Sunday: {e}", err=True)

        typer.echo("")

        # This Friday games
        try:
            friday_games = get_game_schedule(this_friday)
            typer.echo(format_games_output(friday_games, f"This Friday ({this_friday})"))
        except Exception as e:
            typer.echo(f"Error retrieving games for this Friday: {e}", err=True)


if __name__ == "__main__":
    app()
