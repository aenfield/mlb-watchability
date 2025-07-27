"""Game score calculator that orchestrates pNERD and tNERD calculations to produce gNERD scores."""

import os
from dataclasses import dataclass
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from .llm_client import MODEL_STRING_CHEAP, generate_text_from_llm
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
    away_team_nerd_score: float
    home_team_nerd_score: float
    average_team_nerd_score: float

    # Pitcher NERD scores
    away_pitcher_nerd_score: float | None
    home_pitcher_nerd_score: float | None
    average_pitcher_nerd_score: float | None

    # Final game NERD score
    gnerd_score: float

    # Team and pitcher stats objects for this specific game
    away_team_nerd_stats: TeamNerdStats | None
    home_team_nerd_stats: TeamNerdStats | None
    away_pitcher_nerd_stats: PitcherNerdStats | None
    home_pitcher_nerd_stats: PitcherNerdStats | None

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

            # Get team NERD stats and scores
            away_team_nerd_stats = team_nerd_details.get(away_team_abbr)
            home_team_nerd_stats = team_nerd_details.get(home_team_abbr)
            away_team_nerd_score = (
                away_team_nerd_stats.tnerd_score if away_team_nerd_stats else 0.0
            )
            home_team_nerd_score = (
                home_team_nerd_stats.tnerd_score if home_team_nerd_stats else 0.0
            )
            average_team_nerd_score = (away_team_nerd_score + home_team_nerd_score) / 2

            # Get pitcher NERD stats and scores using fuzzy matching
            away_pitcher_nerd_stats = None
            home_pitcher_nerd_stats = None
            away_pitcher_nerd_score = None
            home_pitcher_nerd_score = None
            average_pitcher_nerd_score = None

            if away_starter and away_starter != "TBD":
                away_pitcher_nerd_stats = find_pitcher_nerd_stats_fuzzy(
                    pitcher_nerd_details, away_starter
                )
                if away_pitcher_nerd_stats:
                    away_pitcher_nerd_score = away_pitcher_nerd_stats.pnerd_score

            if home_starter and home_starter != "TBD":
                home_pitcher_nerd_stats = find_pitcher_nerd_stats_fuzzy(
                    pitcher_nerd_details, home_starter
                )
                if home_pitcher_nerd_stats:
                    home_pitcher_nerd_score = home_pitcher_nerd_stats.pnerd_score

            # Calculate average pitcher NERD if we have at least one score
            if (
                away_pitcher_nerd_score is not None
                and home_pitcher_nerd_score is not None
            ):
                average_pitcher_nerd_score = (
                    away_pitcher_nerd_score + home_pitcher_nerd_score
                ) / 2
            elif away_pitcher_nerd_score is not None:
                average_pitcher_nerd_score = away_pitcher_nerd_score
            elif home_pitcher_nerd_score is not None:
                average_pitcher_nerd_score = home_pitcher_nerd_score

            # Calculate final gNERD score
            # gNERD = average of team NERD + average of pitcher NERD
            if average_pitcher_nerd_score is not None:
                gnerd_score = average_team_nerd_score + average_pitcher_nerd_score
            else:
                # If no pitcher data available, use only team NERD
                gnerd_score = average_team_nerd_score

            game_score = cls(
                away_team=away_team,
                home_team=home_team,
                away_starter=away_starter,
                home_starter=home_starter,
                game_time=game_time,
                away_team_nerd_score=away_team_nerd_score,
                home_team_nerd_score=home_team_nerd_score,
                average_team_nerd_score=average_team_nerd_score,
                away_pitcher_nerd_score=away_pitcher_nerd_score,
                home_pitcher_nerd_score=home_pitcher_nerd_score,
                average_pitcher_nerd_score=average_pitcher_nerd_score,
                gnerd_score=gnerd_score,
                away_team_nerd_stats=away_team_nerd_stats,
                home_team_nerd_stats=home_team_nerd_stats,
                away_pitcher_nerd_stats=away_pitcher_nerd_stats,
                home_pitcher_nerd_stats=home_pitcher_nerd_stats,
            )

            game_scores.append(game_score)

        # Sort by gNERD score (highest first)
        game_scores.sort(key=lambda x: x.gnerd_score, reverse=True)

        return game_scores

    def generate_description(
        self, game_date: str | None = None
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Generate an AI-powered description of the game using team and pitcher details.

        Args:
            game_date: Date of the game (optional, for context in prompt)

        Returns:
            Tuple of (generated description string, list of web sources)
            Web sources list will be empty if no web search was performed or no sources found

        Raises:
            FileNotFoundError: If the prompt template file is not found
            Exception: If LLM generation fails
        """

        # Get detailed team and pitcher stats from stored objects
        away_team_stats = self.away_team_nerd_stats
        home_team_stats = self.home_team_nerd_stats
        away_pitcher_stats = self.away_pitcher_nerd_stats
        home_pitcher_stats = self.home_pitcher_nerd_stats

        # Helper function to create team stats dictionary
        def create_team_stats_dict(team_stats: TeamNerdStats | None, prefix: str) -> dict[str, Any]:
            """Create a dictionary of team stats with appropriate prefix."""
            if not team_stats:
                return {
                    f"{prefix}_batting_runs": 0.0,
                    f"{prefix}_z_batting_runs": 0.0,
                    f"{prefix}_barrel_rate": 0.0,
                    f"{prefix}_z_barrel_rate": 0.0,
                    f"{prefix}_baserunning_runs": 0.0,
                    f"{prefix}_z_baserunning_runs": 0.0,
                    f"{prefix}_fielding_runs": 0.0,
                    f"{prefix}_z_fielding_runs": 0.0,
                    f"{prefix}_payroll": 0.0,
                    f"{prefix}_z_payroll": 0.0,
                    f"{prefix}_age": 0.0,
                    f"{prefix}_z_age": 0.0,
                    f"{prefix}_luck": 0.0,
                    f"{prefix}_z_luck": 0.0,
                }

            return {
                f"{prefix}_batting_runs": team_stats.team_stats.batting_runs,
                f"{prefix}_z_batting_runs": team_stats.z_batting_runs,
                f"{prefix}_barrel_rate": team_stats.team_stats.barrel_rate,
                f"{prefix}_z_barrel_rate": team_stats.z_barrel_rate,
                f"{prefix}_baserunning_runs": team_stats.team_stats.baserunning_runs,
                f"{prefix}_z_baserunning_runs": team_stats.z_baserunning_runs,
                f"{prefix}_fielding_runs": team_stats.team_stats.fielding_runs,
                f"{prefix}_z_fielding_runs": team_stats.z_fielding_runs,
                f"{prefix}_payroll": team_stats.team_stats.payroll,
                f"{prefix}_z_payroll": team_stats.z_payroll,
                f"{prefix}_age": team_stats.team_stats.age,
                f"{prefix}_z_age": team_stats.z_age,
                f"{prefix}_luck": team_stats.team_stats.luck,
                f"{prefix}_z_luck": team_stats.z_luck,
            }

        # Helper function to create pitcher stats dictionary
        def create_pitcher_stats_dict(pitcher_stats: PitcherNerdStats | None, prefix: str) -> dict[str, Any]:
            """Create a dictionary of pitcher stats with appropriate prefix."""
            if not pitcher_stats:
                return {
                    f"{prefix}_has_stats": False,
                    f"{prefix}_xfip_minus": 0.0,
                    f"{prefix}_z_xfip_minus": 0.0,
                    f"{prefix}_swinging_strike_rate": 0.0,
                    f"{prefix}_z_swinging_strike_rate": 0.0,
                    f"{prefix}_strike_rate": 0.0,
                    f"{prefix}_z_strike_rate": 0.0,
                    f"{prefix}_velocity": 0.0,
                    f"{prefix}_z_velocity": 0.0,
                    f"{prefix}_age": 0.0,
                    f"{prefix}_z_age": 0.0,
                    f"{prefix}_pace": 0.0,
                    f"{prefix}_z_pace": 0.0,
                    f"{prefix}_luck": 0.0,
                    f"{prefix}_knuckleball_rate": 0.0,
                }

            stats = pitcher_stats.pitcher_stats
            return {
                f"{prefix}_has_stats": True,
                f"{prefix}_xfip_minus": stats.xfip_minus,
                f"{prefix}_z_xfip_minus": pitcher_stats.z_xfip_minus,
                f"{prefix}_swinging_strike_rate": stats.swinging_strike_rate,
                f"{prefix}_z_swinging_strike_rate": pitcher_stats.z_swinging_strike_rate,
                f"{prefix}_strike_rate": stats.strike_rate,
                f"{prefix}_z_strike_rate": pitcher_stats.z_strike_rate,
                f"{prefix}_velocity": stats.velocity,
                f"{prefix}_z_velocity": pitcher_stats.z_velocity,
                f"{prefix}_age": stats.age,
                f"{prefix}_z_age": pitcher_stats.z_age,
                f"{prefix}_pace": stats.pace,
                f"{prefix}_z_pace": pitcher_stats.z_pace,
                f"{prefix}_luck": stats.luck,
                f"{prefix}_knuckleball_rate": stats.knuckleball_rate,
            }

        # Create team and pitcher stats dictionaries and combine all template data
        away_team_data = create_team_stats_dict(away_team_stats, "away")
        home_team_data = create_team_stats_dict(home_team_stats, "home")
        away_pitcher_data = create_pitcher_stats_dict(away_pitcher_stats, "away_pitcher")
        home_pitcher_data = create_pitcher_stats_dict(home_pitcher_stats, "home_pitcher")

        # Set up Jinja2 environment and load template
        template_dir = os.path.dirname(__file__)
        env = Environment(loader=FileSystemLoader(template_dir))

        try:
            template = env.get_template("prompt-game-summary-template.md")
        except TemplateNotFound as e:
            raise FileNotFoundError(f"Prompt template not found: {e}") from e

        # Render the template with Jinja2
        template_data = {
            # Game basics
            "game_date": game_date or "TBD",
            "away_team": self.away_team,
            "home_team": self.home_team,
            "game_time": self.game_time or "TBD",
            "away_starter": self.away_starter or "TBD",
            "home_starter": self.home_starter or "TBD",
            # NERD scores
            "gnerd_score": self.gnerd_score,
            "average_team_nerd": self.average_team_nerd_score,
            "away_team_nerd": self.away_team_nerd_score,
            "home_team_nerd": self.home_team_nerd_score,
            "average_pitcher_nerd": self.average_pitcher_nerd_score or 0.0,
            "away_pitcher_nerd": self.away_pitcher_nerd_score or 0.0,
            "home_pitcher_nerd": self.home_pitcher_nerd_score or 0.0,
        }

        # Add all stats data
        template_data.update(away_team_data)
        template_data.update(home_team_data)
        template_data.update(away_pitcher_data)
        template_data.update(home_pitcher_data)

        formatted_prompt = template.render(template_data)

        # Call the LLM to generate the description
        description, web_sources = generate_text_from_llm(
            prompt=formatted_prompt,
            model=MODEL_STRING_CHEAP,
            max_tokens=300,
            temperature=0.7,
            include_web_search=True,
        )

        return description.strip(), web_sources
