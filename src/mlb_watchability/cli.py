"""Command-line interface for MLB Watchability."""

from datetime import datetime, timedelta
from typing import Any

import typer
from scipy import stats  # type: ignore

from mlb_watchability.data_retrieval import (
    get_all_pitcher_stats,
    get_all_team_stats,
    get_game_schedule,
)
from mlb_watchability.pitcher_stats import calculate_pnerd_score
from mlb_watchability.team_stats import calculate_tnerd_score

app = typer.Typer()


def get_team_abbreviation(full_name: str) -> str:
    """Map full team names to abbreviations used in stats APIs."""
    team_mapping = {
        "Arizona Diamondbacks": "ARI",
        "Atlanta Braves": "ATL",
        "Baltimore Orioles": "BAL",
        "Boston Red Sox": "BOS",
        "Chicago Cubs": "CHC",
        "Chicago White Sox": "CWS",
        "Cincinnati Reds": "CIN",
        "Cleveland Guardians": "CLE",
        "Colorado Rockies": "COL",
        "Detroit Tigers": "DET",
        "Houston Astros": "HOU",
        "Kansas City Royals": "KCR",
        "Los Angeles Angels": "LAA",
        "Los Angeles Dodgers": "LAD",
        "Miami Marlins": "MIA",
        "Milwaukee Brewers": "MIL",
        "Minnesota Twins": "MIN",
        "New York Mets": "NYM",
        "New York Yankees": "NYY",
        "Oakland Athletics": "OAK",
        "Philadelphia Phillies": "PHI",
        "Pittsburgh Pirates": "PIT",
        "San Diego Padres": "SDP",
        "San Francisco Giants": "SFG",
        "Seattle Mariners": "SEA",
        "St. Louis Cardinals": "STL",
        "Tampa Bay Rays": "TBR",
        "Texas Rangers": "TEX",
        "Toronto Blue Jays": "TOR",
        "Washington Nationals": "WSN",
    }
    return team_mapping.get(full_name, full_name)


def calculate_team_nerd_scores(season: int = 2025) -> dict[str, float]:
    """Calculate team NERD scores for all teams."""
    try:
        # Get all team stats - note: payroll data is only available for 2025
        # For other years, we'll use the team batting stats for that year but 2025 payroll/age data
        team_stats_dict = get_all_team_stats(season)

        # Calculate league means and standard deviations
        all_teams = list(team_stats_dict.values())

        # Extract values for each stat
        batting_runs = [team.batting_runs for team in all_teams]
        barrel_rates = [team.barrel_rate for team in all_teams]
        baserunning_runs = [team.baserunning_runs for team in all_teams]
        fielding_runs = [team.fielding_runs for team in all_teams]
        payrolls = [team.payroll for team in all_teams]
        ages = [team.age for team in all_teams]
        luck_values = [team.luck for team in all_teams]

        # Calculate means and standard deviations
        league_means = {
            "batting_runs": stats.tmean(batting_runs),
            "barrel_rate": stats.tmean(barrel_rates),
            "baserunning_runs": stats.tmean(baserunning_runs),
            "fielding_runs": stats.tmean(fielding_runs),
            "payroll": stats.tmean(payrolls),
            "age": stats.tmean(ages),
            "luck": stats.tmean(luck_values),
        }

        league_std_devs = {
            "batting_runs": stats.tstd(batting_runs),
            "barrel_rate": stats.tstd(barrel_rates),
            "baserunning_runs": stats.tstd(baserunning_runs),
            "fielding_runs": stats.tstd(fielding_runs),
            "payroll": stats.tstd(payrolls),
            "age": stats.tstd(ages),
            "luck": stats.tstd(luck_values),
        }

        # Calculate tNERD for each team
        team_nerd_scores = {}
        for team_abbr, team_stats in team_stats_dict.items():
            try:
                team_nerd_stats = calculate_tnerd_score(
                    team_stats, league_means, league_std_devs
                )
                team_nerd_scores[team_abbr] = team_nerd_stats.tnerd_score
            except ValueError:
                # Skip teams with invalid tNERD scores (negative values)
                continue

    except Exception:
        # If calculation fails, return empty dict
        return {}
    else:
        return team_nerd_scores


def calculate_pitcher_nerd_scores(season: int = 2024) -> dict[str, float]:
    """Calculate pitcher NERD scores for all pitchers."""
    try:
        # Get all pitcher stats
        pitcher_stats_dict = get_all_pitcher_stats(season)

        # Calculate league means and standard deviations
        all_pitchers = list(pitcher_stats_dict.values())

        # Extract values for each stat
        xfip_minus_values = [pitcher.xfip_minus for pitcher in all_pitchers]
        swinging_strike_rates = [
            pitcher.swinging_strike_rate for pitcher in all_pitchers
        ]
        strike_rates = [pitcher.strike_rate for pitcher in all_pitchers]
        velocities = [pitcher.velocity for pitcher in all_pitchers]
        ages = [pitcher.age for pitcher in all_pitchers]
        paces = [pitcher.pace for pitcher in all_pitchers]

        # Calculate means and standard deviations
        league_means = {
            "xfip_minus": stats.tmean(xfip_minus_values),
            "swinging_strike_rate": stats.tmean(swinging_strike_rates),
            "strike_rate": stats.tmean(strike_rates),
            "velocity": stats.tmean(velocities),
            "age": stats.tmean(ages),
            "pace": stats.tmean(paces),
        }

        league_std_devs = {
            "xfip_minus": stats.tstd(xfip_minus_values),
            "swinging_strike_rate": stats.tstd(swinging_strike_rates),
            "strike_rate": stats.tstd(strike_rates),
            "velocity": stats.tstd(velocities),
            "age": stats.tstd(ages),
            "pace": stats.tstd(paces),
        }

        # Calculate pNERD for each pitcher
        pitcher_nerd_scores = {}
        for pitcher_name, pitcher_stats in pitcher_stats_dict.items():
            try:
                pitcher_nerd_stats = calculate_pnerd_score(
                    pitcher_stats, league_means, league_std_devs
                )
                pitcher_nerd_scores[pitcher_name] = pitcher_nerd_stats.pnerd_score
            except ValueError:
                # Skip pitchers with invalid pNERD scores (negative values)
                continue

    except Exception:
        # If calculation fails, return empty dict
        return {}
    else:
        return pitcher_nerd_scores


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


@app.command()
def main(
    date: str | None = typer.Argument(
        default=None,
        help="Date to calculate game scores for (YYYY-MM-DD format). Defaults to today and tomorrow.",
    ),
) -> None:
    """Calculate Game NERD scores for MLB games on a given date."""
    if date is not None:
        # Show games for specific date
        try:
            games = get_game_schedule(date)
            season = extract_year_from_date(date)
            team_nerd_scores = calculate_team_nerd_scores(season)
            pitcher_nerd_scores = calculate_pitcher_nerd_scores(season)
            typer.echo(
                format_games_output(games, date, team_nerd_scores, pitcher_nerd_scores)
            )
        except Exception as e:
            typer.echo(f"Error retrieving games for {date}: {e}", err=True)
    else:
        # Show games for today and tomorrow
        today = get_today()
        tomorrow = get_tomorrow()

        typer.echo("MLB Watchability - Game Schedule")
        typer.echo("=" * 40)

        # Calculate team and pitcher NERD scores using today's year
        today_season = extract_year_from_date(today)
        team_nerd_scores = calculate_team_nerd_scores(today_season)
        pitcher_nerd_scores = calculate_pitcher_nerd_scores(today_season)

        # Today's games (with team and pitcher NERD scores)
        try:
            today_games = get_game_schedule(today)
            typer.echo(
                format_games_output(
                    today_games,
                    f"Today ({today})",
                    team_nerd_scores,
                    pitcher_nerd_scores,
                )
            )
        except Exception as e:
            typer.echo(f"Error retrieving games for today: {e}", err=True)

        typer.echo("")

        # Tomorrow's games (without NERD scores)
        try:
            tomorrow_games = get_game_schedule(tomorrow)
            typer.echo(format_games_output(tomorrow_games, f"Tomorrow ({tomorrow})"))
        except Exception as e:
            typer.echo(f"Error retrieving games for tomorrow: {e}", err=True)


if __name__ == "__main__":
    app()
