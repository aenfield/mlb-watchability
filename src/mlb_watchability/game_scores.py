"""Game score calculator that orchestrates pNERD and tNERD calculations to produce gNERD scores."""

import os
from dataclasses import dataclass
from typing import Any

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

    def generate_description(self, game_date: str | None = None) -> tuple[str, list[dict[str, Any]]]:
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
        # Load the prompt template
        template_path = os.path.join(
            os.path.dirname(__file__), "prompt-game-summary-template.md"
        )

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Prompt template not found at {template_path}")

        with open(template_path, encoding="utf-8") as f:
            template = f.read()

        # Get detailed team stats
        away_team_abbr = get_team_abbreviation(self.away_team)
        home_team_abbr = get_team_abbreviation(self.home_team)

        away_team_stats = self.team_nerd_details.get(away_team_abbr)
        home_team_stats = self.team_nerd_details.get(home_team_abbr)

        # Get detailed pitcher stats
        away_pitcher_stats = None
        home_pitcher_stats = None

        if self.away_starter and self.away_starter != "TBD":
            away_pitcher_stats = find_pitcher_nerd_stats_fuzzy(
                self.pitcher_nerd_details, self.away_starter
            )

        if self.home_starter and self.home_starter != "TBD":
            home_pitcher_stats = find_pitcher_nerd_stats_fuzzy(
                self.pitcher_nerd_details, self.home_starter
            )

        # Helper function to create pitcher stats section
        def create_pitcher_stats_section(pitcher_stats: PitcherNerdStats | None) -> str:
            if not pitcher_stats:
                return "No detailed stats available"

            stats = pitcher_stats.pitcher_stats
            return f"""- xFIP-: {stats.xfip_minus:.1f} (z-score: {pitcher_stats.z_xfip_minus:.2f})
- SwStr%: {stats.swinging_strike_rate:.1f}% (z-score: {pitcher_stats.z_swinging_strike_rate:.2f})
- Strike%: {stats.strike_rate:.1f}% (z-score: {pitcher_stats.z_strike_rate:.2f})
- Velocity: {stats.velocity:.1f} mph (z-score: {pitcher_stats.z_velocity:.2f})
- Age: {stats.age} (z-score: {pitcher_stats.z_age:.2f})
- Pace: {stats.pace:.1f}s (z-score: {pitcher_stats.z_pace:.2f})
- Luck: {stats.luck:.1f}
- KN%: {stats.knuckleball_rate:.1f}%"""

        # Format the template with actual values
        formatted_prompt = template.format(
            game_date=game_date or "TBD",
            away_team=self.away_team,
            home_team=self.home_team,
            game_time=self.game_time or "TBD",
            away_starter=self.away_starter or "TBD",
            home_starter=self.home_starter or "TBD",
            gnerd_score=self.gnerd_score,
            average_team_nerd=self.average_team_nerd,
            away_team_nerd=self.away_team_nerd,
            home_team_nerd=self.home_team_nerd,
            average_pitcher_nerd=self.average_pitcher_nerd or 0.0,
            away_pitcher_nerd=self.away_pitcher_nerd or 0.0,
            home_pitcher_nerd=self.home_pitcher_nerd or 0.0,
            # Away team detailed stats
            away_batting_runs=(
                away_team_stats.team_stats.batting_runs if away_team_stats else 0.0
            ),
            away_z_batting_runs=(
                away_team_stats.z_batting_runs if away_team_stats else 0.0
            ),
            away_barrel_rate=(
                away_team_stats.team_stats.barrel_rate if away_team_stats else 0.0
            ),
            away_z_barrel_rate=(
                away_team_stats.z_barrel_rate if away_team_stats else 0.0
            ),
            away_baserunning_runs=(
                away_team_stats.team_stats.baserunning_runs if away_team_stats else 0.0
            ),
            away_z_baserunning_runs=(
                away_team_stats.z_baserunning_runs if away_team_stats else 0.0
            ),
            away_fielding_runs=(
                away_team_stats.team_stats.fielding_runs if away_team_stats else 0.0
            ),
            away_z_fielding_runs=(
                away_team_stats.z_fielding_runs if away_team_stats else 0.0
            ),
            away_payroll=away_team_stats.team_stats.payroll if away_team_stats else 0.0,
            away_z_payroll=away_team_stats.z_payroll if away_team_stats else 0.0,
            away_age=away_team_stats.team_stats.age if away_team_stats else 0.0,
            away_z_age=away_team_stats.z_age if away_team_stats else 0.0,
            away_luck=away_team_stats.team_stats.luck if away_team_stats else 0.0,
            away_z_luck=away_team_stats.z_luck if away_team_stats else 0.0,
            # Home team detailed stats
            home_batting_runs=(
                home_team_stats.team_stats.batting_runs if home_team_stats else 0.0
            ),
            home_z_batting_runs=(
                home_team_stats.z_batting_runs if home_team_stats else 0.0
            ),
            home_barrel_rate=(
                home_team_stats.team_stats.barrel_rate if home_team_stats else 0.0
            ),
            home_z_barrel_rate=(
                home_team_stats.z_barrel_rate if home_team_stats else 0.0
            ),
            home_baserunning_runs=(
                home_team_stats.team_stats.baserunning_runs if home_team_stats else 0.0
            ),
            home_z_baserunning_runs=(
                home_team_stats.z_baserunning_runs if home_team_stats else 0.0
            ),
            home_fielding_runs=(
                home_team_stats.team_stats.fielding_runs if home_team_stats else 0.0
            ),
            home_z_fielding_runs=(
                home_team_stats.z_fielding_runs if home_team_stats else 0.0
            ),
            home_payroll=home_team_stats.team_stats.payroll if home_team_stats else 0.0,
            home_z_payroll=home_team_stats.z_payroll if home_team_stats else 0.0,
            home_age=home_team_stats.team_stats.age if home_team_stats else 0.0,
            home_z_age=home_team_stats.z_age if home_team_stats else 0.0,
            home_luck=home_team_stats.team_stats.luck if home_team_stats else 0.0,
            home_z_luck=home_team_stats.z_luck if home_team_stats else 0.0,
            # Pitcher stats sections
            away_pitcher_stats_section=create_pitcher_stats_section(away_pitcher_stats),
            home_pitcher_stats_section=create_pitcher_stats_section(home_pitcher_stats),
        )

        # Call the LLM to generate the description
        description, web_sources = generate_text_from_llm(
            prompt=formatted_prompt,
            model=MODEL_STRING_CHEAP,
            max_tokens=300,
            temperature=0.7,
            include_web_search=True,
        )

        return description.strip(), web_sources
