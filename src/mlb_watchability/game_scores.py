"""Game score calculator that orchestrates pNERD and tNERD calculations to produce gNERD scores."""

from dataclasses import dataclass
from typing import Any

from .pitcher_stats import (
    PitcherNerdStats,
    calculate_detailed_pitcher_nerd_scores,
    find_pitcher_nerd_stats_fuzzy,
)
from .team_mappings import get_team_abbreviation
from .team_stats import TeamNerdStats, calculate_detailed_team_nerd_scores


@dataclass
class GameScore:
    """
    Data structure for a complete game score calculation.

    Contains team and pitcher information plus calculated NERD scores.
    """

    away_team: str
    home_team: str
    away_starter: str | None
    home_starter: str | None
    game_time: str | None

    # Team NERD scores
    away_team_nerd: float
    home_team_nerd: float
    average_team_nerd: float

    # Pitcher NERD scores
    away_pitcher_nerd: float | None
    home_pitcher_nerd: float | None
    average_pitcher_nerd: float | None

    # Final game NERD score
    gnerd_score: float

    # Detailed stats objects for reference
    team_nerd_details: dict[str, TeamNerdStats]
    pitcher_nerd_details: dict[str, PitcherNerdStats]

    # TODO: This impl below seems like it might be overly complex? And/or what about having the team and
    # pitcher code figure out and make their own game score contributions (while the spec says average of
    # each of team and game and then added together, that really just boils down to 1/4 of each value)

    @classmethod
    def from_games(
        cls, games: list[dict[str, Any]], season: int = 2025
    ) -> list["GameScore"]:
        """
        Calculate gNERD scores for a list of games.

        Args:
            games: List of game dictionaries with team and pitcher information
            season: Season year for statistics calculation

        Returns:
            List of GameScore objects sorted by gNERD score (highest first)
        """
        # Get all team and pitcher NERD scores for the season
        team_nerd_details = calculate_detailed_team_nerd_scores(season)
        pitcher_nerd_details = calculate_detailed_pitcher_nerd_scores(season)

        # Extract team scores for easier lookup
        team_nerd_scores = {
            team: nerd_stats.tnerd_score
            for team, nerd_stats in team_nerd_details.items()
        }

        game_scores = []

        for game in games:
            away_team = game["away_team"]
            home_team = game["home_team"]
            away_starter = game.get("away_starter")
            home_starter = game.get("home_starter")
            game_time = game.get("time")

            # Map team names to abbreviations for NERD score lookup
            away_team_abbr = get_team_abbreviation(away_team)
            home_team_abbr = get_team_abbreviation(home_team)

            # Get team NERD scores
            away_team_nerd = team_nerd_scores.get(away_team_abbr, 0.0)
            home_team_nerd = team_nerd_scores.get(home_team_abbr, 0.0)
            average_team_nerd = (away_team_nerd + home_team_nerd) / 2

            # Get pitcher NERD scores using fuzzy matching
            away_pitcher_nerd = None
            home_pitcher_nerd = None
            average_pitcher_nerd = None

            if away_starter and away_starter != "TBD":
                away_pitcher_stats = find_pitcher_nerd_stats_fuzzy(
                    pitcher_nerd_details, away_starter
                )
                if away_pitcher_stats:
                    away_pitcher_nerd = away_pitcher_stats.pnerd_score

            if home_starter and home_starter != "TBD":
                home_pitcher_stats = find_pitcher_nerd_stats_fuzzy(
                    pitcher_nerd_details, home_starter
                )
                if home_pitcher_stats:
                    home_pitcher_nerd = home_pitcher_stats.pnerd_score

            # Calculate average pitcher NERD if we have at least one score
            if away_pitcher_nerd is not None and home_pitcher_nerd is not None:
                average_pitcher_nerd = (away_pitcher_nerd + home_pitcher_nerd) / 2
            elif away_pitcher_nerd is not None:
                average_pitcher_nerd = away_pitcher_nerd
            elif home_pitcher_nerd is not None:
                average_pitcher_nerd = home_pitcher_nerd

            # Calculate final gNERD score
            # gNERD = average of team NERD + average of pitcher NERD
            if average_pitcher_nerd is not None:
                gnerd_score = average_team_nerd + average_pitcher_nerd
            else:
                # If no pitcher data available, use only team NERD
                gnerd_score = average_team_nerd

            game_score = cls(
                away_team=away_team,
                home_team=home_team,
                away_starter=away_starter,
                home_starter=home_starter,
                game_time=game_time,
                away_team_nerd=away_team_nerd,
                home_team_nerd=home_team_nerd,
                average_team_nerd=average_team_nerd,
                away_pitcher_nerd=away_pitcher_nerd,
                home_pitcher_nerd=home_pitcher_nerd,
                average_pitcher_nerd=average_pitcher_nerd,
                gnerd_score=gnerd_score,
                team_nerd_details=team_nerd_details,
                pitcher_nerd_details=pitcher_nerd_details,
            )

            game_scores.append(game_score)

        # Sort by gNERD score (highest first)
        game_scores.sort(key=lambda x: x.gnerd_score, reverse=True)

        return game_scores
