"""Game score calculator that orchestrates pNERD and tNERD calculations to produce gNERD scores."""

from dataclasses import dataclass
from typing import Any

from .pitcher_stats import calculate_detailed_pitcher_nerd_scores
from .team_mappings import get_team_abbreviation
from .team_stats import calculate_detailed_team_nerd_scores


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


# Claude went to town and to help w/ the issue where the game schedule and pitcher stat data have
# different names (for example, 'Jacob Latz' in the former vs 'Jake Latz' in the latter, 'Michael Soroka'
# vs 'Mike Soroka', 'Jesús Luzardo' vs 'Jesus Luzardo'). I want to think this through a bit more, because
# for example, it shouldn't likely be in game_scores, and I want to keep the original names from the
# data sources (for ex, we need the Fangraph's pitcher data name to form the URL, so wouldn't want to
# replace it), so for now I'll comment this out.
# def normalize_pitcher_name(name: str) -> str:
#     """
#     Normalize pitcher name for better matching between data sources.

#     Handles common variations like:
#     - Accented characters (Jesús -> Jesus)
#     - Formal vs nickname variations (Jacob -> Jake, Michael -> Mike)
#     """
#     if not name:
#         return name

#     # Remove accents and normalize unicode
#     normalized = unicodedata.normalize('NFD', name)
#     normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')

#     # Convert to lowercase for comparison
#     normalized = normalized.lower()

#     # Handle common name variations
#     name_variations = {
#         'jacob': 'jake',
#         'michael': 'mike',
#         'matthew': 'matt',
#         'christopher': 'chris',
#         'benjamin': 'ben',
#         'nicholas': 'nick',
#         'joseph': 'joe',
#         'anthony': 'tony',
#         'jonathan': 'jon',
#         'daniel': 'dan',
#         'david': 'dave',
#         'robert': 'rob',
#         'william': 'will',
#         'alexander': 'alex',
#         'zachary': 'zach',
#     }

#     # Split name into parts
#     parts = normalized.split()
#     if len(parts) >= 2:
#         first_name = parts[0]
#         # Replace formal names with common nicknames
#         if first_name in name_variations:
#             parts[0] = name_variations[first_name]

#     return ' '.join(parts)


# def find_pitcher_score(pitcher_name: str, pitcher_nerd_scores: dict[str, float]) -> float | None:
#     """
#     Find pitcher NERD score with fuzzy name matching.

#     First tries exact match, then tries normalized matching.
#     """
#     if not pitcher_name or pitcher_name == "TBD":
#         return None

#     # Try exact match first
#     if pitcher_name in pitcher_nerd_scores:
#         return pitcher_nerd_scores[pitcher_name]

#     # Try normalized matching
#     normalized_target = normalize_pitcher_name(pitcher_name)

#     for pnerd_pitcher, score in pitcher_nerd_scores.items():
#         normalized_pnerd = normalize_pitcher_name(pnerd_pitcher)
#         if normalized_target == normalized_pnerd:
#             return score

#     return None


# TODO: This impl below seems like it might be overly complex? And/or what about having the team and
# pitcher code figure out and make their own game score contributions (while the spec says average of
# each of team and game and then added together, that really just boils down to 1/4 of each value)


def calculate_game_scores(
    games: list[dict[str, Any]], season: int = 2025
) -> list[GameScore]:
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

    # Extract just the scores for easier lookup
    team_nerd_scores = {
        team: nerd_stats.tnerd_score for team, nerd_stats in team_nerd_details.items()
    }
    pitcher_nerd_scores = {
        pitcher: nerd_stats.pnerd_score
        for pitcher, nerd_stats in pitcher_nerd_details.items()
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

        # Get pitcher NERD scores
        away_pitcher_nerd = None
        home_pitcher_nerd = None
        average_pitcher_nerd = None

        if away_starter and away_starter != "TBD":
            away_pitcher_nerd = pitcher_nerd_scores.get(away_starter)

        if home_starter and home_starter != "TBD":
            home_pitcher_nerd = pitcher_nerd_scores.get(home_starter)

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

        game_score = GameScore(
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
        )

        game_scores.append(game_score)

    # Sort by gNERD score (highest first)
    game_scores.sort(key=lambda x: x.gnerd_score, reverse=True)

    return game_scores
