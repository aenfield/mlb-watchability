"""Data retrieval module for MLB Watchability."""

import zoneinfo
from datetime import datetime
from typing import Any

import pandas as pd
import pybaseball as pb
import statsapi  # type: ignore
from scipy import stats  # type: ignore

from .pitcher_stats import PitcherStats, calculate_pnerd_score
from .team_stats import TeamStats, calculate_tnerd_score


def _raise_missing_columns_error(missing_columns: list[str]) -> None:
    """Raise a RuntimeError for missing columns."""
    raise RuntimeError(f"Missing required columns: {missing_columns}")


def get_game_schedule(date: str) -> list[dict[str, Any]]:
    """
    Retrieve the game schedule for a given date.

    Args:
        date: Date in YYYY-MM-DD format

    Returns:
        List of games with team information and starting pitchers

    Raises:
        ValueError: If date format is invalid
        RuntimeError: If API call fails
    """
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(
            f"Invalid date format. Expected YYYY-MM-DD, got: {date}"
        ) from e

    try:
        # Convert YYYY-MM-DD to MM/DD/YYYY format for MLB-StatsAPI
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        api_date = date_obj.strftime("%m/%d/%Y")

        # Fetch schedule data from MLB-StatsAPI
        schedule_data = statsapi.schedule(start_date=api_date, end_date=api_date)

        # Convert to our expected format
        games = []
        for game in schedule_data:
            # Extract starting pitcher info if available
            away_starter = game.get("away_probable_pitcher") or None
            home_starter = game.get("home_probable_pitcher") or None

            # Format game time if available, convert to Eastern time
            game_time = None
            if "game_datetime" in game:
                try:
                    # Parse UTC datetime
                    game_datetime = game["game_datetime"]
                    if game_datetime.endswith("Z"):
                        # Parse as UTC
                        utc_dt = datetime.strptime(game_datetime, "%Y-%m-%dT%H:%M:%SZ")
                        utc_dt = utc_dt.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
                    else:
                        # Try with timezone info
                        utc_dt = datetime.fromisoformat(
                            game_datetime.replace("Z", "+00:00")
                        )

                    # Convert to Eastern time
                    eastern_tz = zoneinfo.ZoneInfo("America/New_York")
                    eastern_dt = utc_dt.astimezone(eastern_tz)
                    game_time = eastern_dt.strftime("%H:%M")
                except (ValueError, TypeError):
                    game_time = None

            game_dict = {
                "date": date,
                "away_team": game.get("away_name", ""),
                "home_team": game.get("home_name", ""),
                "time": game_time,
                "away_starter": away_starter,
                "home_starter": home_starter,
            }
            games.append(game_dict)

    except Exception as e:
        raise RuntimeError(
            f"Failed to retrieve game schedule for {date}: {str(e)}"
        ) from e
    else:
        return games


def get_all_pitcher_stats(season: int = 2024) -> dict[str, PitcherStats]:
    """
    Retrieve pitcher statistics for all starting pitchers using pybaseball.

    Args:
        season: Season year (default: 2024)

    Returns:
        Dictionary mapping pitcher names to PitcherStats objects

    Raises:
        RuntimeError: If API call fails or data retrieval fails
    """
    try:
        # Fetch pitcher statistics for the season
        # Using qual=20 to get starting pitchers with at least 20 innings pitched
        pitcher_stats_df = pb.pitching_stats(season, qual=20)

        # Filter for starting pitchers only (pitchers with at least 1 game started)
        starting_pitchers = pitcher_stats_df[pitcher_stats_df["GS"] > 0]

        pitcher_stats_dict = {}

        for _, pitcher_row in starting_pitchers.iterrows():
            # Calculate Strike Rate from Strikes/Pitches
            strike_rate = pitcher_row["Strikes"] / pitcher_row["Pitches"]

            # Calculate Luck (ERA- minus xFIP-)
            luck = pitcher_row["ERA-"] - pitcher_row["xFIP-"]

            # Handle KN% NaN values by setting to 0
            kn_rate = pitcher_row.get("KN%", 0.0)
            if pd.isna(kn_rate):
                kn_rate = 0.0

            # Use FBv for velocity as it has better coverage
            velocity = pitcher_row["FBv"]

            # Create PitcherStats object
            pitcher_stats = PitcherStats(
                name=pitcher_row["Name"],
                team=pitcher_row["Team"],
                xfip_minus=pitcher_row["xFIP-"],
                swinging_strike_rate=pitcher_row["SwStr%"],
                strike_rate=strike_rate,
                velocity=velocity,
                age=pitcher_row["Age"],
                pace=pitcher_row["Pace"],
                luck=luck,
                knuckleball_rate=kn_rate,
            )

            pitcher_stats_dict[pitcher_row["Name"]] = pitcher_stats

    except Exception as e:
        raise RuntimeError(
            f"Failed to retrieve pitcher statistics for season {season}: {str(e)}"
        ) from e
    else:
        return pitcher_stats_dict


def get_all_team_stats(season: int = 2025) -> dict[str, TeamStats]:
    """
    Retrieve team statistics for all teams using pybaseball and payroll data.

    Args:
        season: Season year (default: 2025)

    Returns:
        Dictionary mapping team names to TeamStats objects

    Raises:
        RuntimeError: If API call fails or data retrieval fails
    """
    try:
        # Fetch team batting statistics for the season
        team_batting_df = pb.team_batting(season)

        # Load payroll data from CSV file
        payroll_df = pd.read_csv("data/payroll-spotrac.2025.csv")

        # Create team abbreviation mapping for payroll data to match batting stats
        payroll_to_batting_mapping = {
            "TB": "TBR",
            "WSH": "WSN",
            "SD": "SDP",
            "SF": "SFG",
            "KC": "KCR",
        }

        # Apply team name mapping to payroll data
        payroll_df["Team"] = payroll_df["Team"].replace(payroll_to_batting_mapping)

        # Rename Age column in payroll data to avoid conflict
        payroll_df = payroll_df.rename(columns={"Age": "Payroll_Age"})

        # Merge batting stats with payroll data
        merged_df = pd.merge(team_batting_df, payroll_df, on="Team", how="inner")

        # Check for required columns
        required_columns = ["Bat", "Barrel%", "BsR", "Fld", "wRC", "R"]
        missing_columns = [
            col for col in required_columns if col not in merged_df.columns
        ]

        if missing_columns:
            _raise_missing_columns_error(missing_columns)

        team_stats_dict = {}

        for _, team_row in merged_df.iterrows():
            # Calculate luck as wRC minus Runs (opposite of pNERD luck)
            luck = team_row["wRC"] - team_row["R"]

            # Convert payroll from total to millions for readability
            payroll_millions = team_row["Payroll"] / 1_000_000

            # Handle missing Barrel% values
            barrel_rate = team_row.get("Barrel%", 0.0)
            if pd.isna(barrel_rate):
                barrel_rate = 0.0

            # Convert barrel rate from percentage to decimal if needed
            if barrel_rate > 1.0:
                barrel_rate = barrel_rate / 100.0

            # Create TeamStats object
            team_stats = TeamStats(
                name=team_row["Team"],
                batting_runs=team_row["Bat"],
                barrel_rate=barrel_rate,
                baserunning_runs=team_row["BsR"],
                fielding_runs=team_row["Fld"],
                payroll=payroll_millions,
                age=team_row["Payroll_Age"],
                luck=luck,
            )

            team_stats_dict[team_row["Team"]] = team_stats

    except Exception as e:
        raise RuntimeError(
            f"Failed to retrieve team statistics for season {season}: {str(e)}"
        ) from e
    else:
        return team_stats_dict


def calculate_pitcher_nerd_scores(season: int = 2024) -> dict[str, float]:
    """Calculate pitcher NERD scores for all pitchers."""
    detailed_stats = calculate_detailed_pitcher_nerd_scores(season)
    return {pitcher: stats.pnerd_score for pitcher, stats in detailed_stats.items()}


def calculate_detailed_pitcher_nerd_scores(season: int = 2024) -> dict[str, Any]:
    """Calculate detailed pitcher NERD scores for all pitchers."""
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
        pitcher_nerd_details = {}
        for pitcher_name, pitcher_stats in pitcher_stats_dict.items():
            try:
                pitcher_nerd_stats = calculate_pnerd_score(
                    pitcher_stats, league_means, league_std_devs
                )
                pitcher_nerd_details[pitcher_name] = pitcher_nerd_stats
            except ValueError:
                # Skip pitchers with invalid pNERD scores (negative values)
                continue

    except Exception:
        # If calculation fails, return empty dict
        return {}
    else:
        return pitcher_nerd_details


def calculate_team_nerd_scores(season: int = 2025) -> dict[str, float]:
    """Calculate team NERD scores for all teams."""
    detailed_stats = calculate_detailed_team_nerd_scores(season)
    return {team: stats.tnerd_score for team, stats in detailed_stats.items()}


def calculate_detailed_team_nerd_scores(season: int = 2025) -> dict[str, Any]:
    """Calculate detailed team NERD scores for all teams."""
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
        team_nerd_details = {}
        for team_abbr, team_stats in team_stats_dict.items():
            try:
                team_nerd_stats = calculate_tnerd_score(
                    team_stats, league_means, league_std_devs
                )
                team_nerd_details[team_abbr] = team_nerd_stats
            except ValueError:
                # Skip teams with invalid tNERD scores (negative values)
                continue

    except Exception:
        # If calculation fails, return empty dict
        return {}
    else:
        return team_nerd_details
