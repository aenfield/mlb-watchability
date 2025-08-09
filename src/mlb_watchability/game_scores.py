"""Game score calculator that orchestrates pNERD and tNERD calculations to produce gNERD scores."""

import logging
import os
from dataclasses import dataclass
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from .llm_client import (
    ANTHROPIC_MODEL_FULL,
    AnthropicParams,
    OpenAIParams,
    create_llm_client,
)
from .pitcher_stats import (
    PitcherNerdStats,
    calculate_detailed_pitcher_nerd_scores,
    find_pitcher_nerd_stats_fuzzy,
)
from .team_mappings import get_team_abbreviation
from .team_stats import TeamNerdStats, calculate_detailed_team_nerd_scores

logger = logging.getLogger(__name__)

# Field mappings for stats dictionaries
# Format: (field_name, z_score_field_name)
TEAM_STAT_FIELDS: list[tuple[str, str | None]] = [
    ("batting_runs", "z_batting_runs"),
    ("barrel_rate", "z_barrel_rate"),
    ("baserunning_runs", "z_baserunning_runs"),
    ("fielding_runs", "z_fielding_runs"),
    ("payroll", "z_payroll"),
    ("age", "z_age"),
    ("luck", "z_luck"),
]

PITCHER_STAT_FIELDS: list[tuple[str, str | None]] = [
    ("xfip_minus", "z_xfip_minus"),
    ("swinging_strike_rate", "z_swinging_strike_rate"),
    ("strike_rate", "z_strike_rate"),
    ("velocity", "z_velocity"),
    ("age", "z_age"),
    ("pace", "z_pace"),
    ("luck", None),  # No z-score for luck
    ("knuckleball_rate", None),  # No z-score for knuckleball rate
]

# Component field mappings for template data
TEAM_COMPONENT_FIELDS: list[str] = [
    "batting_component",
    "barrel_component",
    "baserunning_component",
    "fielding_component",
    "payroll_component",
    "age_component",
    "luck_component",
    "constant_component",
]

PITCHER_COMPONENT_FIELDS: list[str] = [
    "xfip_component",
    "swinging_strike_component",
    "strike_component",
    "velocity_component",
    "age_component",
    "pace_component",
    "luck_component",
    "knuckleball_component",
    "constant_component",
]

# Standard canned description text used for game summaries
CANNED_GAME_DESCRIPTION = (
    "A concise summary of this compelling matchup, featuring two teams with distinct strengths "
    "and strategic approaches. The visiting team brings their road experience and adaptability, "
    "while the home team looks to leverage familiar surroundings and fan support. Both squads "
    "showcase interesting statistical profiles across pitching, hitting, and defensive metrics. "
    "Key storylines include starting pitcher matchups, offensive production potential, and bullpen "
    "depth. Recent team performance suggests this could be a competitive contest with multiple "
    "momentum shifts. Strategic decisions from both managers will likely play crucial roles in "
    "determining the outcome. Individual player performances could significantly impact team "
    "standings and future positioning. This game represents quality baseball with engaging "
    "narratives for viewers."
)


@dataclass
class AllGamesNerdStats:
    """Statistics about NERD scores across all games."""

    min_gnerd: float
    max_gnerd: float
    avg_gnerd: float
    min_team_nerd: float
    max_team_nerd: float
    avg_team_nerd: float
    min_pitcher_nerd: float
    max_pitcher_nerd: float
    avg_pitcher_nerd: float


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
    game_date: str | None

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

    # Game description and sources
    game_description: str | None = None
    game_description_sources: list[dict[str, Any]] | None = None
    game_description_provider: str | None = None

    # Statistics about all games in this set
    all_games_nerd_stats: AllGamesNerdStats | None = None

    # TODO: This impl below seems like it might be overly complex? And/or what about having the team and
    # pitcher code figure out and make their own game score contributions (while the spec says average of
    # each of team and game and then added together, that really just boils down to 1/4 of each value)

    @classmethod
    def from_games(
        cls,
        games: list[dict[str, Any]],
        season: int = 2025,
        game_desc_source: str | None = None,
        game_desc_limit: int = 1,
        model: str = ANTHROPIC_MODEL_FULL,
        provider: str = "anthropic",
    ) -> list["GameScore"]:
        """
        Calculate gNERD scores for a list of games.

        Args:
            games: List of game dictionaries with team and pitcher information
            season: Season year for statistics calculation
            game_desc_source: Source for game descriptions - None, "canned", or "llm"
            game_desc_limit: Number of top games to generate descriptions for (default 1)
            model: Model to use for LLM descriptions (default ANTHROPIC_MODEL_FULL)
            provider: LLM provider to use for descriptions (default "anthropic")

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
            game_date = game.get("date")

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

            # Calculate average pitcher NERD, using 5.0 as default for missing data
            # Use actual scores if available, otherwise default to 5.0
            away_pitcher_score_final = (
                away_pitcher_nerd_score if away_pitcher_nerd_score is not None else 5.0
            )
            home_pitcher_score_final = (
                home_pitcher_nerd_score if home_pitcher_nerd_score is not None else 5.0
            )
            average_pitcher_nerd_score = (
                away_pitcher_score_final + home_pitcher_score_final
            ) / 2

            # Calculate final gNERD score
            # gNERD = average of team NERD + average of pitcher NERD
            gnerd_score = average_team_nerd_score + average_pitcher_nerd_score

            game_score = cls(
                away_team=away_team,
                home_team=home_team,
                away_starter=away_starter,
                home_starter=home_starter,
                game_time=game_time,
                game_date=game_date,
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

        # Calculate aggregate statistics across all games
        if game_scores:
            gnerd_scores = [gs.gnerd_score for gs in game_scores]
            team_nerd_scores = [gs.away_team_nerd_score for gs in game_scores] + [
                gs.home_team_nerd_score for gs in game_scores
            ]
            pitcher_nerd_scores = [
                score
                for gs in game_scores
                for score in [gs.away_pitcher_nerd_score, gs.home_pitcher_nerd_score]
                if score is not None
            ]

            all_games_stats = AllGamesNerdStats(
                min_gnerd=min(gnerd_scores),
                max_gnerd=max(gnerd_scores),
                avg_gnerd=sum(gnerd_scores) / len(gnerd_scores),
                min_team_nerd=min(team_nerd_scores),
                max_team_nerd=max(team_nerd_scores),
                avg_team_nerd=sum(team_nerd_scores) / len(team_nerd_scores),
                min_pitcher_nerd=(
                    min(pitcher_nerd_scores) if pitcher_nerd_scores else 0.0
                ),
                max_pitcher_nerd=(
                    max(pitcher_nerd_scores) if pitcher_nerd_scores else 0.0
                ),
                avg_pitcher_nerd=(
                    sum(pitcher_nerd_scores) / len(pitcher_nerd_scores)
                    if pitcher_nerd_scores
                    else 0.0
                ),
            )

            # Add the aggregate stats to all game score objects
            for game_score in game_scores:
                game_score.all_games_nerd_stats = all_games_stats

        # Set game descriptions for top games based on game_desc_source parameter
        if game_desc_source is not None:
            for _i, game_score in enumerate(game_scores[:game_desc_limit]):
                if game_desc_source == "canned":
                    game_score.game_description = CANNED_GAME_DESCRIPTION
                    game_score.game_description_sources = []
                elif game_desc_source == "llm":
                    description, sources = game_score.generate_description(
                        model=model, provider=provider
                    )
                    game_score.game_description = description
                    game_score.game_description_sources = sources
                    game_score.game_description_provider = provider

        return game_scores

    def _prepare_template_data(self) -> dict[str, Any]:
        """
        Prepare template data for generating prompts.

        Returns:
            Dictionary of template data including game info, NERD scores, and team/pitcher stats
        """
        # Get detailed team and pitcher stats from stored objects
        away_team_stats = self.away_team_nerd_stats
        home_team_stats = self.home_team_nerd_stats
        away_pitcher_stats = self.away_pitcher_nerd_stats
        home_pitcher_stats = self.home_pitcher_nerd_stats

        # Helper function to create stats dictionary for both teams and pitchers
        def create_stats_dict(
            stats_obj: TeamNerdStats | PitcherNerdStats | None,
            prefix: str,
            field_list: list[tuple[str, str | None]],
            stats_attr: str,
            component_fields: list[str] | None = None,
            extra_fields: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            """Create a dictionary of stats with appropriate prefix."""
            result: dict[str, Any] = extra_fields.copy() if extra_fields else {}

            for field_name, z_field_name in field_list:
                if stats_obj:
                    # Get the actual stat value from the nested stats object
                    stat_source = getattr(stats_obj, stats_attr)
                    result[f"{prefix}_{field_name}"] = getattr(stat_source, field_name)
                    # Get the z-score from the main stats object (if it exists)
                    if z_field_name:
                        result[f"{prefix}_{z_field_name}"] = getattr(
                            stats_obj, z_field_name
                        )
                else:
                    # Use default values when no stats available
                    result[f"{prefix}_{field_name}"] = 0.0
                    if z_field_name:
                        result[f"{prefix}_{z_field_name}"] = 0.0

            # Add component fields if available
            if component_fields and stats_obj:
                for component_field in component_fields:
                    result[f"{prefix}_{component_field}"] = getattr(
                        stats_obj, component_field
                    )
            elif component_fields:
                # Use default values when no stats available
                for component_field in component_fields:
                    result[f"{prefix}_{component_field}"] = 0.0

            return result

        # Helper function to create team stats dictionary
        def create_team_stats_dict(
            team_stats: TeamNerdStats | None, prefix: str
        ) -> dict[str, Any]:
            """Create a dictionary of team stats with appropriate prefix."""
            return create_stats_dict(
                team_stats,
                prefix,
                TEAM_STAT_FIELDS,
                "team_stats",
                TEAM_COMPONENT_FIELDS,
            )

        # Helper function to create pitcher stats dictionary
        def create_pitcher_stats_dict(
            pitcher_stats: PitcherNerdStats | None, prefix: str
        ) -> dict[str, Any]:
            """Create a dictionary of pitcher stats with appropriate prefix."""
            extra_fields = {f"{prefix}_has_stats": pitcher_stats is not None}
            return create_stats_dict(
                pitcher_stats,
                prefix,
                PITCHER_STAT_FIELDS,
                "pitcher_stats",
                PITCHER_COMPONENT_FIELDS,
                extra_fields,
            )

        # Create team and pitcher stats dictionaries
        away_team_data = create_team_stats_dict(away_team_stats, "away")
        home_team_data = create_team_stats_dict(home_team_stats, "home")
        away_pitcher_data = create_pitcher_stats_dict(
            away_pitcher_stats, "away_pitcher"
        )
        home_pitcher_data = create_pitcher_stats_dict(
            home_pitcher_stats, "home_pitcher"
        )

        # Build combined template data
        template_data = {
            # Game basics
            "game_date": self.game_date or "TBD",
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

        # Add aggregate statistics across all games if available
        if self.all_games_nerd_stats:
            template_data.update(
                {
                    "min_gnerd": self.all_games_nerd_stats.min_gnerd,
                    "max_gnerd": self.all_games_nerd_stats.max_gnerd,
                    "avg_gnerd": self.all_games_nerd_stats.avg_gnerd,
                    "min_team_nerd": self.all_games_nerd_stats.min_team_nerd,
                    "max_team_nerd": self.all_games_nerd_stats.max_team_nerd,
                    "avg_team_nerd": self.all_games_nerd_stats.avg_team_nerd,
                    "min_pitcher_nerd": self.all_games_nerd_stats.min_pitcher_nerd,
                    "max_pitcher_nerd": self.all_games_nerd_stats.max_pitcher_nerd,
                    "avg_pitcher_nerd": self.all_games_nerd_stats.avg_pitcher_nerd,
                }
            )

        return template_data

    def _render_prompt_template(self, template_data: dict[str, Any]) -> str:
        """
        Render the Jinja2 prompt template with the provided data.

        Args:
            template_data: Dictionary of data to pass to the template

        Returns:
            Rendered prompt string

        Raises:
            FileNotFoundError: If the prompt template file is not found
        """
        # Set up Jinja2 environment and load template
        template_dir = os.path.dirname(__file__)
        env = Environment(loader=FileSystemLoader(template_dir))

        try:
            template = env.get_template("prompt-game-summary-template.md")
        except TemplateNotFound as e:
            raise FileNotFoundError(f"Prompt template not found: {e}") from e

        return template.render(template_data)

    def generate_formatted_prompt(self) -> str:
        """
        Generate a formatted prompt for the game using template data and Jinja2 rendering.

        Returns:
            Formatted prompt string ready for LLM

        Raises:
            FileNotFoundError: If the prompt template file is not found
        """
        template_data = self._prepare_template_data()
        return self._render_prompt_template(template_data)

    def get_description_from_llm_using_prompt(
        self,
        completed_prompt: str,
        model: str = ANTHROPIC_MODEL_FULL,
        provider: str = "anthropic",
    ) -> tuple[str, list[dict[str, Any]]]:
        """Generate description from LLM using the provided completed prompt."""
        logger.info(f"Retrieving summary for {self.away_team} @ {self.home_team}")

        # Create appropriate parameters based on provider
        params: AnthropicParams | OpenAIParams
        if provider == "anthropic":
            params = AnthropicParams(include_web_search=True)
        elif provider == "openai":
            params = OpenAIParams(include_web_search=True)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # Create client with specified provider and model
        client = create_llm_client(provider=provider, model=model)
        response = client.generate_text(
            prompt=completed_prompt,
            params=params,
        )

        return response.content, response.web_sources or []

    def generate_description(
        self, model: str = ANTHROPIC_MODEL_FULL, provider: str = "anthropic"
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Generate an AI-powered description of the game using team and pitcher details.

        Args:
            model: The model to use for description generation (default: ANTHROPIC_MODEL_FULL)
            provider: The LLM provider to use (default: "anthropic")

        Returns:
            Tuple of (generated description string, list of web sources)
            Web sources list will be empty if no web search was performed or no sources found

        Raises:
            FileNotFoundError: If the prompt template file is not found
            Exception: If LLM generation fails
        """
        formatted_prompt = self.generate_formatted_prompt()

        description, web_sources = self.get_description_from_llm_using_prompt(
            formatted_prompt, model, provider
        )

        # Alternative way to call generate_text_from_llm directly:
        # from .llm_client import AnthropicParams
        # params = AnthropicParams(max_tokens=300, temperature=0.7, include_web_search=True)
        # description, web_sources = generate_text_from_llm(
        #     prompt=formatted_prompt,
        #     params=params,
        #     model=ANTHROPIC_MODEL_CHEAP,
        # )

        return description.strip(), web_sources
