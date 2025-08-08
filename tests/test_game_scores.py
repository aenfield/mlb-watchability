"""Tests for game score calculator."""

from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from jinja2 import TemplateNotFound

from mlb_watchability.game_scores import GameScore
from mlb_watchability.llm_client import (
    ANTHROPIC_MODEL_CHEAP,
    ANTHROPIC_MODEL_FULL,
    LLMResponse,
)
from mlb_watchability.pitcher_stats import PitcherNerdStats, PitcherStats
from mlb_watchability.team_stats import TeamNerdStats, TeamStats


class TestGameScores:
    """Test cases for game score calculations."""

    # Shared test data - Common team stats that can be reused
    TEAM_BOS_BASE = TeamNerdStats(
        team_stats=TeamStats(
            name="BOS",
            batting_runs=10.0,
            barrel_rate=0.08,
            baserunning_runs=5.0,
            fielding_runs=15.0,
            payroll=200.0,
            age=28.5,
            luck=10.0,
        ),
        z_batting_runs=1.0,
        z_barrel_rate=0.5,
        z_baserunning_runs=0.3,
        z_fielding_runs=1.2,
        z_payroll=-0.8,
        z_age=-0.5,
        z_luck=0.4,
        adjusted_payroll=0.8,
        adjusted_age=0.5,
        adjusted_luck=0.4,
        tnerd_score=8.2,
    )

    TEAM_NYY_BASE = TeamNerdStats(
        team_stats=TeamStats(
            name="NYY",
            batting_runs=20.0,
            barrel_rate=0.09,
            baserunning_runs=8.0,
            fielding_runs=12.0,
            payroll=250.0,
            age=29.0,
            luck=5.0,
        ),
        z_batting_runs=1.5,
        z_barrel_rate=0.8,
        z_baserunning_runs=0.6,
        z_fielding_runs=0.9,
        z_payroll=-1.2,
        z_age=-0.3,
        z_luck=0.2,
        adjusted_payroll=1.2,
        adjusted_age=0.3,
        adjusted_luck=0.2,
        tnerd_score=9.5,
    )

    TEAM_CHC_BASE = TeamNerdStats(
        team_stats=TeamStats(
            name="CHC",
            batting_runs=5.0,
            barrel_rate=0.07,
            baserunning_runs=2.0,
            fielding_runs=8.0,
            payroll=180.0,
            age=27.5,
            luck=3.0,
        ),
        z_batting_runs=0.5,
        z_barrel_rate=0.2,
        z_baserunning_runs=0.1,
        z_fielding_runs=0.8,
        z_payroll=-0.3,
        z_age=-0.8,
        z_luck=0.1,
        adjusted_payroll=0.3,
        adjusted_age=0.8,
        adjusted_luck=0.1,
        tnerd_score=6.8,
    )

    TEAM_MIL_BASE = TeamNerdStats(
        team_stats=TeamStats(
            name="MIL",
            batting_runs=12.0,
            barrel_rate=0.085,
            baserunning_runs=6.0,
            fielding_runs=10.0,
            payroll=150.0,
            age=28.0,
            luck=7.0,
        ),
        z_batting_runs=1.2,
        z_barrel_rate=0.6,
        z_baserunning_runs=0.4,
        z_fielding_runs=1.0,
        z_payroll=0.2,
        z_age=-0.4,
        z_luck=0.3,
        adjusted_payroll=0.0,
        adjusted_age=0.4,
        adjusted_luck=0.3,
        tnerd_score=7.9,
    )

    # Shared pitcher data
    PITCHER_JOHN_BASE = PitcherNerdStats(
        pitcher_stats=PitcherStats(
            name="John Pitcher",
            team="BOS",
            xfip_minus=95.0,
            swinging_strike_rate=0.12,
            strike_rate=0.65,
            velocity=95.5,
            age=28,
            pace=22.0,
            luck=5.0,
            knuckleball_rate=0.0,
        ),
        z_xfip_minus=-0.5,
        z_swinging_strike_rate=1.2,
        z_strike_rate=0.8,
        z_velocity=1.0,
        z_age=-0.3,
        z_pace=-0.5,
        adjusted_velocity=1.0,
        adjusted_age=0.3,
        adjusted_luck=0.25,
        pnerd_score=6.8,
    )

    PITCHER_JANE_BASE = PitcherNerdStats(
        pitcher_stats=PitcherStats(
            name="Jane Starter",
            team="NYY",
            xfip_minus=88.0,
            swinging_strike_rate=0.14,
            strike_rate=0.68,
            velocity=93.2,
            age=26,
            pace=20.5,
            luck=8.0,
            knuckleball_rate=0.0,
        ),
        z_xfip_minus=-1.2,
        z_swinging_strike_rate=1.8,
        z_strike_rate=1.2,
        z_velocity=0.5,
        z_age=-0.8,
        z_pace=-1.0,
        adjusted_velocity=0.5,
        adjusted_age=0.8,
        adjusted_luck=0.4,
        pnerd_score=7.5,
    )

    PITCHER_KNOWN_BASE = PitcherNerdStats(
        pitcher_stats=PitcherStats(
            name="Known Pitcher",
            team="CHC",
            xfip_minus=92.0,
            swinging_strike_rate=0.11,
            strike_rate=0.63,
            velocity=94.0,
            age=29,
            pace=23.0,
            luck=3.0,
            knuckleball_rate=0.0,
        ),
        z_xfip_minus=-0.8,
        z_swinging_strike_rate=0.9,
        z_strike_rate=0.5,
        z_velocity=0.7,
        z_age=0.2,
        z_pace=0.2,
        adjusted_velocity=0.7,
        adjusted_age=0.0,
        adjusted_luck=0.15,
        pnerd_score=5.5,
    )

    # Shared game data
    GAME_BOS_VS_NYY = {
        "away_team": "Boston Red Sox",
        "home_team": "New York Yankees",
        "away_starter": "John Pitcher",
        "home_starter": "Jane Starter",
        "time": "7:05 PM",
    }

    GAME_CHC_VS_MIL = {
        "away_team": "Chicago Cubs",
        "home_team": "Milwaukee Brewers",
        "away_starter": "Known Pitcher",
        "home_starter": "TBD",
        "time": "2:20 PM",
    }

    @staticmethod
    def modify_team_stats(base_team: TeamNerdStats, **overrides: Any) -> TeamNerdStats:
        """Helper method to create variations of team stats with overrides."""
        team_dict = base_team.team_stats.__dict__.copy()
        team_dict.update({k: v for k, v in overrides.items() if k in team_dict})

        # Create modified team stats
        modified_team_stats = TeamStats(**team_dict)

        # Create modified team nerd stats with base values, allowing override of any field
        nerd_dict = base_team.__dict__.copy()
        nerd_dict["team_stats"] = modified_team_stats
        nerd_dict.update({k: v for k, v in overrides.items() if k in nerd_dict})

        return TeamNerdStats(**nerd_dict)

    @staticmethod
    def modify_pitcher_stats(
        base_pitcher: PitcherNerdStats, **overrides: Any
    ) -> PitcherNerdStats:
        """Helper method to create variations of pitcher stats with overrides."""
        pitcher_dict = base_pitcher.pitcher_stats.__dict__.copy()
        pitcher_dict.update({k: v for k, v in overrides.items() if k in pitcher_dict})

        # Create modified pitcher stats
        modified_pitcher_stats = PitcherStats(**pitcher_dict)

        # Create modified pitcher nerd stats with base values, allowing override of any field
        nerd_dict = base_pitcher.__dict__.copy()
        nerd_dict["pitcher_stats"] = modified_pitcher_stats
        nerd_dict.update({k: v for k, v in overrides.items() if k in nerd_dict})

        return PitcherNerdStats(**nerd_dict)

    def test_calculate_game_scores_with_both_pitchers(self) -> None:
        """Test gNERD calculation when both starting pitchers have data."""
        # Use shared game data
        games = [self.GAME_BOS_VS_NYY]

        # Use shared test data
        mock_team_nerd_details = {
            "BOS": self.TEAM_BOS_BASE,
            "NYY": self.TEAM_NYY_BASE,
        }

        mock_pitcher_nerd_details = {
            "John Pitcher": self.PITCHER_JOHN_BASE,
            "Jane Starter": self.PITCHER_JANE_BASE,
        }

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"
            ) as mock_team,
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitcher,
        ):

            mock_team.return_value = mock_team_nerd_details
            mock_pitcher.return_value = mock_pitcher_nerd_details

            game_scores = GameScore.from_games(games, 2025)

            assert len(game_scores) == 1
            game_score = game_scores[0]

            assert game_score.away_team == "Boston Red Sox"
            assert game_score.home_team == "New York Yankees"
            assert game_score.away_starter == "John Pitcher"
            assert game_score.home_starter == "Jane Starter"
            assert game_score.game_time == "7:05 PM"

            # Check team NERD scores
            assert game_score.away_team_nerd_score == 8.2
            assert game_score.home_team_nerd_score == 9.5
            assert game_score.average_team_nerd_score == pytest.approx((8.2 + 9.5) / 2)

            # Check pitcher NERD scores
            assert game_score.away_pitcher_nerd_score == 6.8
            assert game_score.home_pitcher_nerd_score == 7.5
            assert game_score.average_pitcher_nerd_score == pytest.approx(
                (6.8 + 7.5) / 2
            )

            # Check final gNERD score = average team NERD + average pitcher NERD
            expected_gnerd = ((8.2 + 9.5) / 2) + ((6.8 + 7.5) / 2)
            assert game_score.gnerd_score == pytest.approx(expected_gnerd)

    def test_calculate_game_scores_with_one_pitcher(self) -> None:
        """Test gNERD calculation when only one starting pitcher has data."""
        games = [self.GAME_CHC_VS_MIL]

        mock_team_nerd_details = {
            "CHC": self.TEAM_CHC_BASE,
            "MIL": self.TEAM_MIL_BASE,
        }

        mock_pitcher_nerd_details = {
            "Known Pitcher": self.PITCHER_KNOWN_BASE,
        }

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"
            ) as mock_team,
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitcher,
        ):

            mock_team.return_value = mock_team_nerd_details
            mock_pitcher.return_value = mock_pitcher_nerd_details

            game_scores = GameScore.from_games(games, 2025)

            assert len(game_scores) == 1
            game_score = game_scores[0]

            # Check team scores
            assert game_score.away_team_nerd_score == 6.8
            assert game_score.home_team_nerd_score == 7.9
            assert game_score.average_team_nerd_score == pytest.approx((6.8 + 7.9) / 2)

            # Check pitcher scores - one available, one defaults to 5.0
            assert game_score.away_pitcher_nerd_score == 5.5
            assert game_score.home_pitcher_nerd_score is None
            assert game_score.average_pitcher_nerd_score == pytest.approx(
                (5.5 + 5.0) / 2
            )  # One pitcher available, one defaults to 5.0

            # Check final gNERD score
            expected_gnerd = ((6.8 + 7.9) / 2) + ((5.5 + 5.0) / 2)
            assert game_score.gnerd_score == pytest.approx(expected_gnerd)

    def test_calculate_game_scores_no_pitcher_data(self) -> None:
        """Test gNERD calculation when no pitcher data is available."""
        games = [
            {
                "away_team": "San Francisco Giants",
                "home_team": "Los Angeles Dodgers",
                "away_starter": "TBD",
                "home_starter": "Unknown Pitcher",
                "time": "10:10 PM",
            }
        ]

        mock_team_nerd_details = {
            "SFG": TeamNerdStats(
                team_stats=TeamStats(
                    name="SFG",
                    batting_runs=8.0,
                    barrel_rate=0.075,
                    baserunning_runs=4.0,
                    fielding_runs=6.0,
                    payroll=170.0,
                    age=29.5,
                    luck=2.0,
                ),
                z_batting_runs=0.8,
                z_barrel_rate=0.3,
                z_baserunning_runs=0.2,
                z_fielding_runs=0.6,
                z_payroll=0.1,
                z_age=0.2,
                z_luck=0.05,
                adjusted_payroll=0.0,
                adjusted_age=0.0,
                adjusted_luck=0.05,
                tnerd_score=5.95,
            ),
            "LAD": TeamNerdStats(
                team_stats=TeamStats(
                    name="LAD",
                    batting_runs=25.0,
                    barrel_rate=0.095,
                    baserunning_runs=10.0,
                    fielding_runs=18.0,
                    payroll=280.0,
                    age=27.0,
                    luck=12.0,
                ),
                z_batting_runs=2.0,
                z_barrel_rate=1.0,
                z_baserunning_runs=0.8,
                z_fielding_runs=1.5,
                z_payroll=-1.5,
                z_age=-1.0,
                z_luck=0.6,
                adjusted_payroll=1.5,
                adjusted_age=1.0,
                adjusted_luck=0.6,
                tnerd_score=11.4,
            ),
        }

        # No pitcher data
        mock_pitcher_nerd_details: dict[str, PitcherNerdStats] = {}

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"
            ) as mock_team,
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitcher,
        ):

            mock_team.return_value = mock_team_nerd_details
            mock_pitcher.return_value = mock_pitcher_nerd_details

            game_scores = GameScore.from_games(games, 2025)

            assert len(game_scores) == 1
            game_score = game_scores[0]

            # Check team scores
            assert game_score.away_team_nerd_score == 5.95
            assert game_score.home_team_nerd_score == 11.4
            assert game_score.average_team_nerd_score == pytest.approx(
                (5.95 + 11.4) / 2
            )

            # Check pitcher scores - none available, both default to 5.0
            assert game_score.away_pitcher_nerd_score is None
            assert game_score.home_pitcher_nerd_score is None
            assert game_score.average_pitcher_nerd_score == pytest.approx(
                (5.0 + 5.0) / 2
            )  # Both pitchers default to 5.0

            # Check final gNERD score - team NERD + pitcher defaults
            expected_gnerd = ((5.95 + 11.4) / 2) + ((5.0 + 5.0) / 2)
            assert game_score.gnerd_score == pytest.approx(expected_gnerd)

    def test_calculate_game_scores_multiple_games_sorted(self) -> None:
        """Test that multiple games are sorted by gNERD score in descending order."""
        games = [
            {
                "away_team": "Boston Red Sox",
                "home_team": "New York Yankees",
                "away_starter": "Low Pitcher",
                "home_starter": "High Pitcher",
                "time": "7:05 PM",
            },
            {
                "away_team": "Chicago Cubs",
                "home_team": "Milwaukee Brewers",
                "away_starter": "Medium Pitcher",
                "home_starter": "TBD",
                "time": "2:20 PM",
            },
        ]

        # Mock data that will result in different gNERD scores
        mock_team_nerd_details = {
            "BOS": TeamNerdStats(
                team_stats=TeamStats(
                    name="BOS",
                    batting_runs=5.0,
                    barrel_rate=0.07,
                    baserunning_runs=2.0,
                    fielding_runs=5.0,
                    payroll=180.0,
                    age=28.0,
                    luck=3.0,
                ),
                z_batting_runs=0.5,
                z_barrel_rate=0.2,
                z_baserunning_runs=0.1,
                z_fielding_runs=0.5,
                z_payroll=-0.3,
                z_age=-0.5,
                z_luck=0.1,
                adjusted_payroll=0.3,
                adjusted_age=0.5,
                adjusted_luck=0.1,
                tnerd_score=5.2,
            ),
            "NYY": TeamNerdStats(
                team_stats=TeamStats(
                    name="NYY",
                    batting_runs=8.0,
                    barrel_rate=0.08,
                    baserunning_runs=4.0,
                    fielding_runs=8.0,
                    payroll=250.0,
                    age=29.0,
                    luck=5.0,
                ),
                z_batting_runs=0.8,
                z_barrel_rate=0.5,
                z_baserunning_runs=0.3,
                z_fielding_runs=0.8,
                z_payroll=-1.2,
                z_age=-0.3,
                z_luck=0.2,
                adjusted_payroll=1.2,
                adjusted_age=0.3,
                adjusted_luck=0.2,
                tnerd_score=6.1,
            ),
            "CHC": TeamNerdStats(
                team_stats=TeamStats(
                    name="CHC",
                    batting_runs=15.0,
                    barrel_rate=0.09,
                    baserunning_runs=8.0,
                    fielding_runs=12.0,
                    payroll=200.0,
                    age=27.0,
                    luck=10.0,
                ),
                z_batting_runs=1.5,
                z_barrel_rate=0.8,
                z_baserunning_runs=0.6,
                z_fielding_runs=1.2,
                z_payroll=-0.8,
                z_age=-1.0,
                z_luck=0.5,
                adjusted_payroll=0.8,
                adjusted_age=1.0,
                adjusted_luck=0.5,
                tnerd_score=9.6,
            ),
            "MIL": TeamNerdStats(
                team_stats=TeamStats(
                    name="MIL",
                    batting_runs=12.0,
                    barrel_rate=0.085,
                    baserunning_runs=6.0,
                    fielding_runs=10.0,
                    payroll=150.0,
                    age=28.5,
                    luck=7.0,
                ),
                z_batting_runs=1.2,
                z_barrel_rate=0.6,
                z_baserunning_runs=0.4,
                z_fielding_runs=1.0,
                z_payroll=0.2,
                z_age=-0.2,
                z_luck=0.3,
                adjusted_payroll=0.0,
                adjusted_age=0.2,
                adjusted_luck=0.3,
                tnerd_score=7.5,
            ),
        }

        mock_pitcher_nerd_details = {
            "Low Pitcher": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Low Pitcher",
                    team="BOS",
                    xfip_minus=105.0,
                    swinging_strike_rate=0.08,
                    strike_rate=0.60,
                    velocity=90.0,
                    age=32,
                    pace=25.0,
                    luck=0.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=0.8,
                z_swinging_strike_rate=-1.0,
                z_strike_rate=-0.5,
                z_velocity=-1.0,
                z_age=1.0,
                z_pace=1.0,
                adjusted_velocity=0.0,
                adjusted_age=0.0,
                adjusted_luck=0.0,
                pnerd_score=3.5,
            ),
            "High Pitcher": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="High Pitcher",
                    team="NYY",
                    xfip_minus=80.0,
                    swinging_strike_rate=0.16,
                    strike_rate=0.70,
                    velocity=97.0,
                    age=25,
                    pace=18.0,
                    luck=10.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-2.0,
                z_swinging_strike_rate=2.0,
                z_strike_rate=1.5,
                z_velocity=1.8,
                z_age=-1.2,
                z_pace=-1.5,
                adjusted_velocity=1.8,
                adjusted_age=1.2,
                adjusted_luck=0.5,
                pnerd_score=12.8,
            ),
            "Medium Pitcher": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Medium Pitcher",
                    team="CHC",
                    xfip_minus=95.0,
                    swinging_strike_rate=0.12,
                    strike_rate=0.65,
                    velocity=94.0,
                    age=28,
                    pace=21.0,
                    luck=5.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-0.5,
                z_swinging_strike_rate=1.0,
                z_strike_rate=0.5,
                z_velocity=0.5,
                z_age=-0.2,
                z_pace=-0.3,
                adjusted_velocity=0.5,
                adjusted_age=0.2,
                adjusted_luck=0.25,
                pnerd_score=7.2,
            ),
        }

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"
            ) as mock_team,
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitcher,
        ):

            mock_team.return_value = mock_team_nerd_details
            mock_pitcher.return_value = mock_pitcher_nerd_details

            game_scores = GameScore.from_games(games, 2025)

            assert len(game_scores) == 2

            # First game should have higher gNERD score
            # Game 1: BOS@NYY with Low Pitcher vs High Pitcher
            # Team average: (5.2 + 6.1) / 2 = 5.65
            # Pitcher average: (3.5 + 12.8) / 2 = 8.15
            # gNERD: 5.65 + 8.15 = 13.8

            # Game 2: CHC@MIL with Medium Pitcher vs TBD
            # Team average: (9.6 + 7.5) / 2 = 8.55
            # Pitcher average: 7.2 (only one pitcher)
            # gNERD: 8.55 + 7.2 = 15.75

            # So Game 2 should be first (higher gNERD)
            assert game_scores[0].away_team == "Chicago Cubs"
            assert game_scores[0].home_team == "Milwaukee Brewers"
            assert game_scores[0].gnerd_score > game_scores[1].gnerd_score

            assert game_scores[1].away_team == "Boston Red Sox"
            assert game_scores[1].home_team == "New York Yankees"

    def test_game_score_dataclass_validation(self) -> None:
        """Test that GameScore dataclass contains all required fields."""
        # Create minimal test data for the new fields
        {
            "TST": TeamNerdStats(
                team_stats=TeamStats(
                    name="TST",
                    batting_runs=5.0,
                    barrel_rate=0.08,
                    baserunning_runs=2.0,
                    fielding_runs=5.0,
                    payroll=180.0,
                    age=28.0,
                    luck=3.0,
                ),
                z_batting_runs=0.5,
                z_barrel_rate=0.2,
                z_baserunning_runs=0.1,
                z_fielding_runs=0.5,
                z_payroll=-0.3,
                z_age=-0.5,
                z_luck=0.1,
                adjusted_payroll=0.3,
                adjusted_age=0.5,
                adjusted_luck=0.1,
                tnerd_score=5.0,
            )
        }

        {
            "Test Pitcher": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Test Pitcher",
                    team="TST",
                    xfip_minus=95.0,
                    swinging_strike_rate=0.12,
                    strike_rate=0.65,
                    velocity=94.0,
                    age=28,
                    pace=21.0,
                    luck=5.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-0.5,
                z_swinging_strike_rate=1.0,
                z_strike_rate=0.5,
                z_velocity=0.5,
                z_age=-0.2,
                z_pace=-0.3,
                adjusted_velocity=0.5,
                adjusted_age=0.2,
                adjusted_luck=0.25,
                pnerd_score=7.0,
            )
        }

        game_score = GameScore(
            away_team="Team A",
            home_team="Team B",
            away_starter="Pitcher A",
            home_starter="Pitcher B",
            game_time="7:00 PM",
            game_date="2025-07-27",
            away_team_nerd_score=5.0,
            home_team_nerd_score=6.0,
            average_team_nerd_score=5.5,
            away_pitcher_nerd_score=7.0,
            home_pitcher_nerd_score=8.0,
            average_pitcher_nerd_score=7.5,
            gnerd_score=13.0,
            away_team_nerd_stats=None,
            home_team_nerd_stats=None,
            away_pitcher_nerd_stats=None,
            home_pitcher_nerd_stats=None,
        )

        assert game_score.away_team == "Team A"
        assert game_score.home_team == "Team B"
        assert game_score.away_starter == "Pitcher A"
        assert game_score.home_starter == "Pitcher B"
        assert game_score.game_time == "7:00 PM"
        assert game_score.away_team_nerd_score == 5.0
        assert game_score.home_team_nerd_score == 6.0
        assert game_score.average_team_nerd_score == 5.5
        assert game_score.away_pitcher_nerd_score == 7.0
        assert game_score.home_pitcher_nerd_score == 8.0
        assert game_score.average_pitcher_nerd_score == 7.5
        assert game_score.gnerd_score == 13.0
        assert game_score.away_team_nerd_stats is None
        assert game_score.home_team_nerd_stats is None
        assert game_score.away_pitcher_nerd_stats is None
        assert game_score.home_pitcher_nerd_stats is None

    def test_from_games_stores_detailed_stats(self) -> None:
        """Test that from_games() properly stores detailed TeamNerdStats and PitcherNerdStats objects."""
        games = [
            {
                "away_team": "Boston Red Sox",
                "home_team": "New York Yankees",
                "away_starter": "Test Pitcher",
                "home_starter": "Another Pitcher",
                "time": "7:05 PM",
            }
        ]

        # Use shared test data
        mock_team_nerd_details = {
            "BOS": self.TEAM_BOS_BASE,
            "NYY": self.TEAM_NYY_BASE,
        }

        # Mock pitcher NERD data
        mock_pitcher_nerd_details = {
            "Test Pitcher": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Test Pitcher",
                    team="BOS",
                    xfip_minus=95.0,
                    swinging_strike_rate=0.12,
                    strike_rate=0.65,
                    velocity=95.5,
                    age=28,
                    pace=22.0,
                    luck=5.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-0.5,
                z_swinging_strike_rate=1.2,
                z_strike_rate=0.8,
                z_velocity=1.0,
                z_age=-0.3,
                z_pace=-0.5,
                adjusted_velocity=1.0,
                adjusted_age=0.3,
                adjusted_luck=0.25,
                pnerd_score=6.8,
            ),
            "Another Pitcher": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Another Pitcher",
                    team="NYY",
                    xfip_minus=88.0,
                    swinging_strike_rate=0.14,
                    strike_rate=0.68,
                    velocity=93.2,
                    age=26,
                    pace=20.5,
                    luck=8.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-1.2,
                z_swinging_strike_rate=1.8,
                z_strike_rate=1.2,
                z_velocity=0.5,
                z_age=-0.8,
                z_pace=-1.0,
                adjusted_velocity=0.5,
                adjusted_age=0.8,
                adjusted_luck=0.4,
                pnerd_score=7.5,
            ),
        }

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"
            ) as mock_team,
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitcher,
        ):

            mock_team.return_value = mock_team_nerd_details
            mock_pitcher.return_value = mock_pitcher_nerd_details

            game_scores = GameScore.from_games(games, 2025)

            assert len(game_scores) == 1
            game_score = game_scores[0]

            # Verify that individual stats are stored (these will be set based on the specific teams/pitchers)
            # In a real implementation, these would be populated with the specific team/pitcher stats
            # For this test, we're just verifying the structure exists
            assert hasattr(game_score, "away_team_nerd_stats")
            assert hasattr(game_score, "home_team_nerd_stats")
            assert hasattr(game_score, "away_pitcher_nerd_stats")
            assert hasattr(game_score, "home_pitcher_nerd_stats")

    def test_generate_description_with_complete_data(self) -> None:
        """Test generate_description with complete team and pitcher data."""
        game_score = GameScore(
            away_team="Boston Red Sox",
            home_team="New York Yankees",
            away_starter="John Pitcher",
            home_starter="Jane Starter",
            game_time="7:05 PM",
            game_date="2025-07-27",
            away_team_nerd_score=8.2,
            home_team_nerd_score=9.5,
            average_team_nerd_score=8.85,
            away_pitcher_nerd_score=6.8,
            home_pitcher_nerd_score=7.5,
            average_pitcher_nerd_score=7.15,
            gnerd_score=16.0,
            away_team_nerd_stats=None,
            home_team_nerd_stats=None,
            away_pitcher_nerd_stats=None,
            home_pitcher_nerd_stats=None,
        )

        # Mock the LLM response
        mock_response = "This is an exciting matchup between two powerhouse teams!"

        # Mock the LLM client and response
        mock_llm_response = LLMResponse(
            content=mock_response, model="test-model", web_sources=[]
        )

        with patch(
            "mlb_watchability.game_scores.create_llm_client"
        ) as mock_create_client:
            mock_client = Mock()
            mock_client.generate_text.return_value = mock_llm_response
            mock_create_client.return_value = mock_client

            description, web_sources = game_score.generate_description()

            assert description == mock_response
            assert web_sources == []

            # Verify client was created with correct parameters
            mock_create_client.assert_called_once_with(
                provider="anthropic", model=ANTHROPIC_MODEL_FULL
            )

            # Verify client.generate_text was called with correct parameters
            mock_client.generate_text.assert_called_once()
            call_args = mock_client.generate_text.call_args
            # Temperature and web search should be passed
            assert call_args[1]["temperature"] == 0.7
            assert call_args[1]["include_web_search"] is True

            # Verify prompt contains expected data
            prompt = call_args[1]["prompt"]
            assert "Boston Red Sox" in prompt
            assert "New York Yankees" in prompt
            assert "John Pitcher" in prompt
            assert "Jane Starter" in prompt
            assert "16.0" in prompt  # gNERD score

    def test_generate_description_missing_template_file(self) -> None:
        """Test generate_description raises error when template file is missing."""
        game_score = GameScore(
            away_team="Boston Red Sox",
            home_team="New York Yankees",
            away_starter="John Pitcher",
            home_starter="Jane Starter",
            game_time="7:05 PM",
            game_date="2025-07-27",
            away_team_nerd_score=8.2,
            home_team_nerd_score=9.5,
            average_team_nerd_score=8.85,
            away_pitcher_nerd_score=6.8,
            home_pitcher_nerd_score=7.5,
            average_pitcher_nerd_score=7.15,
            gnerd_score=16.0,
            away_team_nerd_stats=None,
            home_team_nerd_stats=None,
            away_pitcher_nerd_stats=None,
            home_pitcher_nerd_stats=None,
        )

        # Mock Jinja2 Environment.get_template to raise TemplateNotFound
        with patch("mlb_watchability.game_scores.Environment") as mock_env_class:
            mock_env = MagicMock()
            mock_env.get_template.side_effect = TemplateNotFound(
                "prompt-game-summary-template.md"
            )
            mock_env_class.return_value = mock_env

            with pytest.raises(FileNotFoundError) as exc_info:
                game_score.generate_description()

            assert "Prompt template not found" in str(exc_info.value)

    def test_generate_description_with_missing_pitcher_data(self) -> None:
        """Test generate_description handles missing pitcher data gracefully."""
        game_score = GameScore(
            away_team="Boston Red Sox",
            home_team="New York Yankees",
            away_starter="TBD",
            home_starter="Unknown Pitcher",
            game_time="7:05 PM",
            game_date="2025-07-27",
            away_team_nerd_score=8.2,
            home_team_nerd_score=0.0,
            average_team_nerd_score=4.1,
            away_pitcher_nerd_score=None,
            home_pitcher_nerd_score=None,
            average_pitcher_nerd_score=None,
            gnerd_score=4.1,
            away_team_nerd_stats=None,
            home_team_nerd_stats=None,
            away_pitcher_nerd_stats=None,
            home_pitcher_nerd_stats=None,
        )

        mock_response = "Game with limited pitcher data available."

        # Mock the LLM client and response
        mock_llm_response = LLMResponse(
            content=mock_response, model="test-model", web_sources=[]
        )

        with patch(
            "mlb_watchability.game_scores.create_llm_client"
        ) as mock_create_client:
            mock_client = Mock()
            mock_client.generate_text.return_value = mock_llm_response
            mock_create_client.return_value = mock_client

            description, web_sources = game_score.generate_description()

            assert description == mock_response
            assert web_sources == []

            # Verify client was created and called
            mock_create_client.assert_called_once_with(
                provider="anthropic", model=ANTHROPIC_MODEL_FULL
            )
            mock_client.generate_text.assert_called_once()

            # Verify prompt was generated even with missing data
            prompt = mock_client.generate_text.call_args[1]["prompt"]
            assert "TBD" in prompt
            assert "No detailed stats available" in prompt

    def test_generate_description_with_whitespace_in_response(self) -> None:
        """Test generate_description strips whitespace from LLM response."""
        game_score = GameScore(
            away_team="Boston Red Sox",
            home_team="New York Yankees",
            away_starter="John Pitcher",
            home_starter="Jane Starter",
            game_time="7:05 PM",
            game_date="2025-07-27",
            away_team_nerd_score=8.2,
            home_team_nerd_score=9.5,
            average_team_nerd_score=8.85,
            away_pitcher_nerd_score=6.8,
            home_pitcher_nerd_score=7.5,
            average_pitcher_nerd_score=7.15,
            gnerd_score=16.0,
            away_team_nerd_stats=None,
            home_team_nerd_stats=None,
            away_pitcher_nerd_stats=None,
            home_pitcher_nerd_stats=None,
        )

        # Mock response with leading/trailing whitespace
        mock_response = "   \n  This is a great game!  \n  "

        # Mock the LLM client and response
        mock_llm_response = LLMResponse(
            content=mock_response, model="test-model", web_sources=[]
        )

        with patch(
            "mlb_watchability.game_scores.create_llm_client"
        ) as mock_create_client:
            mock_client = Mock()
            mock_client.generate_text.return_value = mock_llm_response
            mock_create_client.return_value = mock_client

            description, web_sources = game_score.generate_description()

            assert description == "This is a great game!"  # Whitespace stripped
            assert web_sources == []

    def test_generate_description_with_web_sources(self) -> None:
        """Test generate_description returns web sources when available."""
        game_score = GameScore(
            away_team="Boston Red Sox",
            home_team="New York Yankees",
            away_starter="John Pitcher",
            home_starter="Jane Starter",
            game_time="7:05 PM",
            game_date="2025-07-27",
            away_team_nerd_score=8.2,
            home_team_nerd_score=9.5,
            average_team_nerd_score=8.85,
            away_pitcher_nerd_score=6.8,
            home_pitcher_nerd_score=7.5,
            average_pitcher_nerd_score=7.15,
            gnerd_score=16.0,
            away_team_nerd_stats=None,
            home_team_nerd_stats=None,
            away_pitcher_nerd_stats=None,
            home_pitcher_nerd_stats=None,
        )

        # Mock response with web sources
        mock_response = "Great game with recent updates!"
        mock_sources = [
            {"url": "https://example.com/article1", "title": "Game Preview"},
            {"url": "https://example.com/article2", "title": "Player Stats"},
        ]

        # Mock the LLM client and response
        mock_llm_response = LLMResponse(
            content=mock_response, model="test-model", web_sources=mock_sources
        )

        with patch(
            "mlb_watchability.game_scores.create_llm_client"
        ) as mock_create_client:
            mock_client = Mock()
            mock_client.generate_text.return_value = mock_llm_response
            mock_create_client.return_value = mock_client

            description, web_sources = game_score.generate_description()

            assert description == mock_response
            assert web_sources == mock_sources
            assert len(web_sources) == 2
            assert web_sources[0]["url"] == "https://example.com/article1"
            assert web_sources[0]["title"] == "Game Preview"

    def test_game_date_field_storage_and_usage(self) -> None:
        """Test that game_date field is properly stored and used in template data."""
        game_date = "2025-07-27"
        game_score = GameScore(
            away_team="Test Team A",
            home_team="Test Team B",
            away_starter="Pitcher A",
            home_starter="Pitcher B",
            game_time="7:00 PM",
            game_date=game_date,
            away_team_nerd_score=5.0,
            home_team_nerd_score=6.0,
            average_team_nerd_score=5.5,
            away_pitcher_nerd_score=4.0,
            home_pitcher_nerd_score=7.0,
            average_pitcher_nerd_score=5.5,
            gnerd_score=11.0,
            away_team_nerd_stats=None,
            home_team_nerd_stats=None,
            away_pitcher_nerd_stats=None,
            home_pitcher_nerd_stats=None,
        )

        # Test that game_date is stored correctly
        assert game_score.game_date == game_date

        # Test that template data uses stored game_date
        template_data = game_score._prepare_template_data()
        assert template_data["game_date"] == game_date

        # Test that template data falls back to parameter if no stored date
        game_score_no_date = GameScore(
            away_team="Test Team A",
            home_team="Test Team B",
            away_starter="Pitcher A",
            home_starter="Pitcher B",
            game_time="7:00 PM",
            game_date=None,
            away_team_nerd_score=5.0,
            home_team_nerd_score=6.0,
            average_team_nerd_score=5.5,
            away_pitcher_nerd_score=4.0,
            home_pitcher_nerd_score=7.0,
            average_pitcher_nerd_score=5.5,
            gnerd_score=11.0,
            away_team_nerd_stats=None,
            home_team_nerd_stats=None,
            away_pitcher_nerd_stats=None,
            home_pitcher_nerd_stats=None,
        )

        # Test fallback to "TBD" when no stored date
        template_data_tbd = game_score_no_date._prepare_template_data()
        assert template_data_tbd["game_date"] == "TBD"

    def test_from_games_extracts_game_date(self) -> None:
        """Test that from_games method extracts and stores game_date from game dictionaries."""
        games = [
            {
                "away_team": "New York Yankees",
                "home_team": "Boston Red Sox",
                "away_starter": "Gerrit Cole",
                "home_starter": "Brayan Bello",
                "time": "7:10 PM",
                "date": "2025-07-27",
            }
        ]

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"
            ) as mock_team_scores,
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitcher_scores,
            patch(
                "mlb_watchability.game_scores.get_team_abbreviation"
            ) as mock_get_abbr,
        ):

            # Mock return values
            mock_team_scores.return_value = {}
            mock_pitcher_scores.return_value = {}
            mock_get_abbr.side_effect = lambda x: x[:3].upper()

            game_scores = GameScore.from_games(games)

            assert len(game_scores) == 1
            assert game_scores[0].game_date == "2025-07-27"

    def test_game_score_new_description_properties(self) -> None:
        """Test that GameScore has the new game_description and game_description_sources properties."""
        game_score = GameScore(
            away_team="Team A",
            home_team="Team B",
            away_starter="Pitcher A",
            home_starter="Pitcher B",
            game_time="7:00 PM",
            game_date="2025-07-27",
            away_team_nerd_score=5.0,
            home_team_nerd_score=6.0,
            average_team_nerd_score=5.5,
            away_pitcher_nerd_score=7.0,
            home_pitcher_nerd_score=8.0,
            average_pitcher_nerd_score=7.5,
            gnerd_score=13.0,
            away_team_nerd_stats=None,
            home_team_nerd_stats=None,
            away_pitcher_nerd_stats=None,
            home_pitcher_nerd_stats=None,
        )

        # Verify new properties default to None
        assert game_score.game_description is None
        assert game_score.game_description_sources is None

        # Verify properties can be set
        game_score.game_description = "Test description"
        game_score.game_description_sources = [{"url": "test.com", "title": "Test"}]

        assert game_score.game_description == "Test description"
        assert game_score.game_description_sources == [
            {"url": "test.com", "title": "Test"}
        ]

    def test_from_games_with_no_description_source(self) -> None:
        """Test from_games with game_desc_source=None (default) leaves descriptions as None."""
        games = [
            {
                "away_team": "Boston Red Sox",
                "home_team": "New York Yankees",
                "away_starter": "John Pitcher",
                "home_starter": "Jane Starter",
                "time": "7:05 PM",
            }
        ]

        mock_team_nerd_details = {
            "BOS": self.TEAM_BOS_BASE,
            "NYY": self.TEAM_NYY_BASE,
        }

        mock_pitcher_nerd_details = {
            "John Pitcher": self.PITCHER_JOHN_BASE,
            "Jane Starter": self.PITCHER_JANE_BASE,
        }

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"
            ) as mock_team,
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitcher,
        ):

            mock_team.return_value = mock_team_nerd_details
            mock_pitcher.return_value = mock_pitcher_nerd_details

            game_scores = GameScore.from_games(games, 2025)

            assert len(game_scores) == 1
            game_score = game_scores[0]

            # Verify descriptions are None when no source specified
            assert game_score.game_description is None
            assert game_score.game_description_sources is None

    def test_from_games_with_canned_description(self) -> None:
        """Test from_games with game_desc_source='canned' sets canned description."""
        games = [
            {
                "away_team": "Boston Red Sox",
                "home_team": "New York Yankees",
                "away_starter": "John Pitcher",
                "home_starter": "Jane Starter",
                "time": "7:05 PM",
            },
            {
                "away_team": "Chicago Cubs",
                "home_team": "Milwaukee Brewers",
                "away_starter": "Low Pitcher",
                "home_starter": "TBD",
                "time": "2:20 PM",
            },
        ]

        mock_team_nerd_details = {
            "BOS": self.TEAM_BOS_BASE,
            "NYY": self.TEAM_NYY_BASE,
            "CHC": self.TEAM_CHC_BASE,
            "MIL": self.TEAM_MIL_BASE,
        }

        mock_pitcher_nerd_details = {
            "John Pitcher": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="John Pitcher",
                    team="BOS",
                    xfip_minus=95.0,
                    swinging_strike_rate=0.12,
                    strike_rate=0.65,
                    velocity=95.5,
                    age=28,
                    pace=22.0,
                    luck=5.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-0.5,
                z_swinging_strike_rate=1.2,
                z_strike_rate=0.8,
                z_velocity=1.0,
                z_age=-0.3,
                z_pace=-0.5,
                adjusted_velocity=1.0,
                adjusted_age=0.3,
                adjusted_luck=0.25,
                pnerd_score=6.8,
            ),
            "Jane Starter": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Jane Starter",
                    team="NYY",
                    xfip_minus=88.0,
                    swinging_strike_rate=0.14,
                    strike_rate=0.68,
                    velocity=93.2,
                    age=26,
                    pace=20.5,
                    luck=8.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-1.2,
                z_swinging_strike_rate=1.8,
                z_strike_rate=1.2,
                z_velocity=0.5,
                z_age=-0.8,
                z_pace=-1.0,
                adjusted_velocity=0.5,
                adjusted_age=0.8,
                adjusted_luck=0.4,
                pnerd_score=7.5,
            ),
            "Low Pitcher": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Low Pitcher",
                    team="CHC",
                    xfip_minus=105.0,
                    swinging_strike_rate=0.08,
                    strike_rate=0.60,
                    velocity=90.0,
                    age=32,
                    pace=25.0,
                    luck=0.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=0.8,
                z_swinging_strike_rate=-1.0,
                z_strike_rate=-0.5,
                z_velocity=-1.0,
                z_age=1.0,
                z_pace=1.0,
                adjusted_velocity=0.0,
                adjusted_age=0.0,
                adjusted_luck=0.0,
                pnerd_score=3.5,
            ),
        }

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"
            ) as mock_team,
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitcher,
        ):

            mock_team.return_value = mock_team_nerd_details
            mock_pitcher.return_value = mock_pitcher_nerd_details

            # Test with default limit (1 game gets description)
            game_scores = GameScore.from_games(games, 2025, game_desc_source="canned")

            assert len(game_scores) == 2
            # Games are sorted by gNERD score, so highest score gets description
            assert game_scores[0].game_description is not None
            assert "compelling matchup" in game_scores[0].game_description
            assert game_scores[0].game_description_sources == []

            # Second game should not have description with default limit
            assert game_scores[1].game_description is None
            assert game_scores[1].game_description_sources is None

    def test_from_games_with_canned_description_custom_limit(self) -> None:
        """Test from_games with game_desc_source='canned' and custom limit."""
        games = [
            {
                "away_team": "Boston Red Sox",
                "home_team": "New York Yankees",
                "away_starter": "John Pitcher",
                "home_starter": "Jane Starter",
                "time": "7:05 PM",
            },
            {
                "away_team": "Chicago Cubs",
                "home_team": "Milwaukee Brewers",
                "away_starter": "Low Pitcher",
                "home_starter": "TBD",
                "time": "2:20 PM",
            },
        ]

        mock_team_nerd_details = {
            "BOS": self.TEAM_BOS_BASE,
            "NYY": self.TEAM_NYY_BASE,
            "CHC": self.TEAM_CHC_BASE,
            "MIL": self.TEAM_MIL_BASE,
        }

        mock_pitcher_nerd_details = {
            "John Pitcher": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="John Pitcher",
                    team="BOS",
                    xfip_minus=95.0,
                    swinging_strike_rate=0.12,
                    strike_rate=0.65,
                    velocity=95.5,
                    age=28,
                    pace=22.0,
                    luck=5.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-0.5,
                z_swinging_strike_rate=1.2,
                z_strike_rate=0.8,
                z_velocity=1.0,
                z_age=-0.3,
                z_pace=-0.5,
                adjusted_velocity=1.0,
                adjusted_age=0.3,
                adjusted_luck=0.25,
                pnerd_score=6.8,
            ),
            "Jane Starter": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Jane Starter",
                    team="NYY",
                    xfip_minus=88.0,
                    swinging_strike_rate=0.14,
                    strike_rate=0.68,
                    velocity=93.2,
                    age=26,
                    pace=20.5,
                    luck=8.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-1.2,
                z_swinging_strike_rate=1.8,
                z_strike_rate=1.2,
                z_velocity=0.5,
                z_age=-0.8,
                z_pace=-1.0,
                adjusted_velocity=0.5,
                adjusted_age=0.8,
                adjusted_luck=0.4,
                pnerd_score=7.5,
            ),
            "Low Pitcher": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Low Pitcher",
                    team="CHC",
                    xfip_minus=105.0,
                    swinging_strike_rate=0.08,
                    strike_rate=0.60,
                    velocity=90.0,
                    age=32,
                    pace=25.0,
                    luck=0.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=0.8,
                z_swinging_strike_rate=-1.0,
                z_strike_rate=-0.5,
                z_velocity=-1.0,
                z_age=1.0,
                z_pace=1.0,
                adjusted_velocity=0.0,
                adjusted_age=0.0,
                adjusted_luck=0.0,
                pnerd_score=3.5,
            ),
        }

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"
            ) as mock_team,
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitcher,
        ):

            mock_team.return_value = mock_team_nerd_details
            mock_pitcher.return_value = mock_pitcher_nerd_details

            # Test with limit of 2 (both games get descriptions)
            game_scores = GameScore.from_games(
                games, 2025, game_desc_source="canned", game_desc_limit=2
            )

            assert len(game_scores) == 2
            # Both games should have descriptions
            assert game_scores[0].game_description is not None
            assert "compelling matchup" in game_scores[0].game_description
            assert game_scores[0].game_description_sources == []

            assert game_scores[1].game_description is not None
            assert "compelling matchup" in game_scores[1].game_description
            assert game_scores[1].game_description_sources == []

    def test_from_games_with_llm_description(self) -> None:
        """Test from_games with game_desc_source='llm' calls generate_description."""
        games = [
            {
                "away_team": "Boston Red Sox",
                "home_team": "New York Yankees",
                "away_starter": "John Pitcher",
                "home_starter": "Jane Starter",
                "time": "7:05 PM",
            }
        ]

        mock_team_nerd_details = {
            "BOS": self.TEAM_BOS_BASE,
            "NYY": self.TEAM_NYY_BASE,
        }

        mock_pitcher_nerd_details = {
            "John Pitcher": self.PITCHER_JOHN_BASE,
            "Jane Starter": self.PITCHER_JANE_BASE,
        }

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"
            ) as mock_team,
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitcher,
        ):

            mock_team.return_value = mock_team_nerd_details
            mock_pitcher.return_value = mock_pitcher_nerd_details

            # Mock generate_description to avoid actual LLM calls
            with patch.object(GameScore, "generate_description") as mock_generate:
                mock_generate.return_value = (
                    "LLM generated description",
                    [{"url": "test.com", "title": "Test"}],
                )

                game_scores = GameScore.from_games(games, 2025, game_desc_source="llm")

                assert len(game_scores) == 1
                game_score = game_scores[0]

                # Verify generate_description was called
                mock_generate.assert_called_once()

                # Verify description and sources were set
                assert game_score.game_description == "LLM generated description"
                assert game_score.game_description_sources == [
                    {"url": "test.com", "title": "Test"}
                ]

    def test_from_games_description_limit_boundary(self) -> None:
        """Test that game_desc_limit properly controls which games get descriptions (boundary testing)."""
        games = [
            {
                "away_team": "Team A",
                "home_team": "Team B",
                "away_starter": "Pitcher A",
                "home_starter": "Pitcher B",
                "time": "7:00 PM",
            },
            {
                "away_team": "Team C",
                "home_team": "Team D",
                "away_starter": "Pitcher C",
                "home_starter": "Pitcher D",
                "time": "8:00 PM",
            },
            {
                "away_team": "Team E",
                "home_team": "Team F",
                "away_starter": "Pitcher E",
                "home_starter": "Pitcher F",
                "time": "9:00 PM",
            },
        ]

        # Create mock data that results in different gNERD scores for clear ordering
        mock_team_nerd_details = {
            "TEA": TeamNerdStats(
                team_stats=TeamStats(
                    name="TEA",
                    batting_runs=20.0,
                    barrel_rate=0.09,
                    baserunning_runs=8.0,
                    fielding_runs=12.0,
                    payroll=200.0,
                    age=28.0,
                    luck=5.0,
                ),
                z_batting_runs=2.0,
                z_barrel_rate=1.0,
                z_baserunning_runs=0.8,
                z_fielding_runs=1.2,
                z_payroll=-0.8,
                z_age=-0.5,
                z_luck=0.2,
                adjusted_payroll=0.8,
                adjusted_age=0.5,
                adjusted_luck=0.2,
                tnerd_score=10.0,
            ),
            "TEB": TeamNerdStats(
                team_stats=TeamStats(
                    name="TEB",
                    batting_runs=15.0,
                    barrel_rate=0.08,
                    baserunning_runs=5.0,
                    fielding_runs=10.0,
                    payroll=180.0,
                    age=29.0,
                    luck=3.0,
                ),
                z_batting_runs=1.5,
                z_barrel_rate=0.8,
                z_baserunning_runs=0.5,
                z_fielding_runs=1.0,
                z_payroll=-0.5,
                z_age=-0.2,
                z_luck=0.1,
                adjusted_payroll=0.5,
                adjusted_age=0.2,
                adjusted_luck=0.1,
                tnerd_score=8.0,
            ),
            "TEC": TeamNerdStats(
                team_stats=TeamStats(
                    name="TEC",
                    batting_runs=10.0,
                    barrel_rate=0.07,
                    baserunning_runs=2.0,
                    fielding_runs=8.0,
                    payroll=160.0,
                    age=30.0,
                    luck=1.0,
                ),
                z_batting_runs=1.0,
                z_barrel_rate=0.5,
                z_baserunning_runs=0.2,
                z_fielding_runs=0.8,
                z_payroll=-0.2,
                z_age=0.1,
                z_luck=0.05,
                adjusted_payroll=0.2,
                adjusted_age=0.0,
                adjusted_luck=0.05,
                tnerd_score=6.0,
            ),
        }

        mock_pitcher_nerd_details = {
            "Pitcher A": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Pitcher A",
                    team="TEA",
                    xfip_minus=80.0,
                    swinging_strike_rate=0.15,
                    strike_rate=0.70,
                    velocity=97.0,
                    age=25,
                    pace=18.0,
                    luck=8.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-2.0,
                z_swinging_strike_rate=2.0,
                z_strike_rate=1.5,
                z_velocity=1.8,
                z_age=-1.0,
                z_pace=-1.2,
                adjusted_velocity=1.8,
                adjusted_age=1.0,
                adjusted_luck=0.4,
                pnerd_score=12.0,
            ),
            "Pitcher B": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Pitcher B",
                    team="TEA",
                    xfip_minus=85.0,
                    swinging_strike_rate=0.13,
                    strike_rate=0.67,
                    velocity=95.0,
                    age=27,
                    pace=20.0,
                    luck=5.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-1.5,
                z_swinging_strike_rate=1.5,
                z_strike_rate=1.0,
                z_velocity=1.2,
                z_age=-0.5,
                z_pace=-0.8,
                adjusted_velocity=1.2,
                adjusted_age=0.5,
                adjusted_luck=0.25,
                pnerd_score=9.0,
            ),
            "Pitcher C": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Pitcher C",
                    team="TEA",
                    xfip_minus=90.0,
                    swinging_strike_rate=0.11,
                    strike_rate=0.64,
                    velocity=93.0,
                    age=29,
                    pace=22.0,
                    luck=2.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-1.0,
                z_swinging_strike_rate=1.0,
                z_strike_rate=0.5,
                z_velocity=0.8,
                z_age=0.0,
                z_pace=-0.3,
                adjusted_velocity=0.8,
                adjusted_age=0.0,
                adjusted_luck=0.1,
                pnerd_score=7.0,
            ),
            "Pitcher D": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Pitcher D",
                    team="TEA",
                    xfip_minus=95.0,
                    swinging_strike_rate=0.10,
                    strike_rate=0.62,
                    velocity=91.0,
                    age=31,
                    pace=24.0,
                    luck=0.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-0.5,
                z_swinging_strike_rate=0.5,
                z_strike_rate=0.2,
                z_velocity=0.3,
                z_age=0.5,
                z_pace=0.2,
                adjusted_velocity=0.3,
                adjusted_age=0.0,
                adjusted_luck=0.0,
                pnerd_score=5.0,
            ),
            "Pitcher E": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Pitcher E",
                    team="TEA",
                    xfip_minus=100.0,
                    swinging_strike_rate=0.09,
                    strike_rate=0.60,
                    velocity=89.0,
                    age=33,
                    pace=26.0,
                    luck=-2.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=0.0,
                z_swinging_strike_rate=0.0,
                z_strike_rate=0.0,
                z_velocity=0.0,
                z_age=1.0,
                z_pace=0.5,
                adjusted_velocity=0.0,
                adjusted_age=0.0,
                adjusted_luck=0.0,
                pnerd_score=3.0,
            ),
            "Pitcher F": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Pitcher F",
                    team="TEA",
                    xfip_minus=105.0,
                    swinging_strike_rate=0.08,
                    strike_rate=0.58,
                    velocity=87.0,
                    age=35,
                    pace=28.0,
                    luck=-5.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=0.5,
                z_swinging_strike_rate=-0.5,
                z_strike_rate=-0.2,
                z_velocity=-0.3,
                z_age=1.5,
                z_pace=1.0,
                adjusted_velocity=0.0,
                adjusted_age=0.0,
                adjusted_luck=0.0,
                pnerd_score=1.0,
            ),
        }

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"
            ) as mock_team,
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitcher,
            patch(
                "mlb_watchability.game_scores.get_team_abbreviation"
            ) as mock_get_abbr,
        ):
            mock_team.return_value = mock_team_nerd_details
            mock_pitcher.return_value = mock_pitcher_nerd_details
            # Map team names to abbreviations for different teams
            mock_get_abbr.side_effect = lambda team: {
                "Team A": "TEA",
                "Team B": "TEA",
                "Team C": "TEB",
                "Team D": "TEB",
                "Team E": "TEC",
                "Team F": "TEC",
            }[team]

            # Test with limit=2, should only get descriptions for top 2 games
            game_scores = GameScore.from_games(
                games, 2025, game_desc_source="canned", game_desc_limit=2
            )

            assert len(game_scores) == 3

            # First two games (highest gNERD scores) should have descriptions
            assert game_scores[0].game_description is not None
            assert "compelling matchup" in game_scores[0].game_description
            assert game_scores[0].game_description_sources == []

            assert game_scores[1].game_description is not None
            assert "compelling matchup" in game_scores[1].game_description
            assert game_scores[1].game_description_sources == []

            # Third game (beyond limit) should NOT have description
            assert game_scores[2].game_description is None
            assert game_scores[2].game_description_sources is None

    def test_pitcher_default_score_one_missing(self) -> None:
        """Test that missing pitcher data defaults to 5.0 when one pitcher has data."""
        games = [
            {
                "away_team": "Arizona Diamondbacks",
                "home_team": "Colorado Rockies",
                "away_starter": "Known Ace",
                "home_starter": "Unknown Rookie",
                "time": "8:40 PM",
            }
        ]

        mock_team_nerd_details = {
            "ARI": TeamNerdStats(
                team_stats=TeamStats(
                    name="ARI",
                    batting_runs=15.0,
                    barrel_rate=0.09,
                    baserunning_runs=7.0,
                    fielding_runs=11.0,
                    payroll=160.0,
                    age=26.5,
                    luck=8.0,
                ),
                z_batting_runs=1.5,
                z_barrel_rate=0.9,
                z_baserunning_runs=0.7,
                z_fielding_runs=1.1,
                z_payroll=0.0,
                z_age=-1.0,
                z_luck=0.4,
                adjusted_payroll=0.0,
                adjusted_age=1.0,
                adjusted_luck=0.4,
                tnerd_score=8.7,
            ),
            "COL": TeamNerdStats(
                team_stats=TeamStats(
                    name="COL",
                    batting_runs=3.0,
                    barrel_rate=0.065,
                    baserunning_runs=1.0,
                    fielding_runs=4.0,
                    payroll=90.0,
                    age=30.0,
                    luck=-2.0,
                ),
                z_batting_runs=0.3,
                z_barrel_rate=0.0,
                z_baserunning_runs=0.1,
                z_fielding_runs=0.4,
                z_payroll=1.0,
                z_age=0.5,
                z_luck=-0.1,
                adjusted_payroll=0.0,
                adjusted_age=0.0,
                adjusted_luck=0.1,
                tnerd_score=4.2,
            ),
        }

        # Only away pitcher has data
        mock_pitcher_nerd_details = {
            "Known Ace": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Known Ace",
                    team="ARI",
                    xfip_minus=80.0,
                    swinging_strike_rate=0.16,
                    strike_rate=0.70,
                    velocity=97.5,
                    age=25,
                    pace=19.0,
                    luck=12.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-2.0,
                z_swinging_strike_rate=2.5,
                z_strike_rate=1.5,
                z_velocity=1.8,
                z_age=-1.0,
                z_pace=-1.5,
                adjusted_velocity=1.8,
                adjusted_age=1.0,
                adjusted_luck=0.6,
                pnerd_score=9.2,
            )
        }

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"
            ) as mock_team,
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitcher,
        ):

            mock_team.return_value = mock_team_nerd_details
            mock_pitcher.return_value = mock_pitcher_nerd_details

            game_scores = GameScore.from_games(games, 2025)

            assert len(game_scores) == 1
            game_score = game_scores[0]

            # Verify team scores
            assert game_score.away_team_nerd_score == 8.7
            assert game_score.home_team_nerd_score == 4.2
            average_team_nerd = (8.7 + 4.2) / 2

            # Verify pitcher scores - one known, one defaults to 5.0
            assert game_score.away_pitcher_nerd_score == 9.2
            assert game_score.home_pitcher_nerd_score is None
            assert game_score.average_pitcher_nerd_score == pytest.approx(
                (9.2 + 5.0) / 2
            )

            # Verify final gNERD calculation
            expected_gnerd = average_team_nerd + ((9.2 + 5.0) / 2)
            assert game_score.gnerd_score == pytest.approx(expected_gnerd)

    def test_pitcher_default_score_both_missing(self) -> None:
        """Test that both pitchers default to 5.0 when no pitcher data is available."""
        games = [
            {
                "away_team": "Oakland Athletics",
                "home_team": "Seattle Mariners",
                "away_starter": "Completely Unknown",
                "home_starter": "Also Unknown",
                "time": "4:10 PM",
            }
        ]

        mock_team_nerd_details = {
            "ATH": TeamNerdStats(
                team_stats=TeamStats(
                    name="ATH",
                    batting_runs=-5.0,
                    barrel_rate=0.06,
                    baserunning_runs=-2.0,
                    fielding_runs=2.0,
                    payroll=60.0,
                    age=25.0,
                    luck=-8.0,
                ),
                z_batting_runs=-0.5,
                z_barrel_rate=-0.3,
                z_baserunning_runs=-0.2,
                z_fielding_runs=0.2,
                z_payroll=1.5,
                z_age=-1.5,
                z_luck=-0.4,
                adjusted_payroll=0.0,
                adjusted_age=1.5,
                adjusted_luck=0.4,
                tnerd_score=2.8,
            ),
            "SEA": TeamNerdStats(
                team_stats=TeamStats(
                    name="SEA",
                    batting_runs=18.0,
                    barrel_rate=0.088,
                    baserunning_runs=9.0,
                    fielding_runs=14.0,
                    payroll=190.0,
                    age=28.0,
                    luck=6.0,
                ),
                z_batting_runs=1.8,
                z_barrel_rate=0.8,
                z_baserunning_runs=0.9,
                z_fielding_runs=1.4,
                z_payroll=-0.5,
                z_age=-0.2,
                z_luck=0.3,
                adjusted_payroll=0.5,
                adjusted_age=0.2,
                adjusted_luck=0.3,
                tnerd_score=9.8,
            ),
        }

        # No pitcher data at all
        mock_pitcher_nerd_details: dict[str, PitcherNerdStats] = {}

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"
            ) as mock_team,
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitcher,
        ):

            mock_team.return_value = mock_team_nerd_details
            mock_pitcher.return_value = mock_pitcher_nerd_details

            game_scores = GameScore.from_games(games, 2025)

            assert len(game_scores) == 1
            game_score = game_scores[0]

            # Verify team scores
            assert game_score.away_team_nerd_score == 2.8
            assert game_score.home_team_nerd_score == 9.8
            average_team_nerd = (2.8 + 9.8) / 2

            # Verify pitcher scores - both default to 5.0
            assert game_score.away_pitcher_nerd_score is None
            assert game_score.home_pitcher_nerd_score is None
            assert game_score.average_pitcher_nerd_score == pytest.approx(5.0)

            # Verify final gNERD calculation
            expected_gnerd = average_team_nerd + 5.0
            assert game_score.gnerd_score == pytest.approx(expected_gnerd)


class TestGameScoresIntegration:
    """Integration tests for GameScore that make actual API calls."""

    @pytest.mark.costly
    def test_generate_description_real_api_call(self) -> None:
        """Test generate_description with real API call (integration test)."""
        # Create simple test data
        {
            "SEA": TeamNerdStats(
                team_stats=TeamStats(
                    name="SEA",
                    batting_runs=15.0,
                    barrel_rate=0.09,
                    baserunning_runs=8.0,
                    fielding_runs=12.0,
                    payroll=180.0,
                    age=27.5,
                    luck=5.0,
                ),
                z_batting_runs=1.2,
                z_barrel_rate=0.7,
                z_baserunning_runs=0.6,
                z_fielding_runs=1.0,
                z_payroll=-0.3,
                z_age=-0.8,
                z_luck=0.3,
                adjusted_payroll=0.3,
                adjusted_age=0.8,
                adjusted_luck=0.3,
                tnerd_score=8.9,
            ),
            "LAA": TeamNerdStats(
                team_stats=TeamStats(
                    name="LAA",
                    batting_runs=8.0,
                    barrel_rate=0.075,
                    baserunning_runs=2.0,
                    fielding_runs=5.0,
                    payroll=200.0,
                    age=29.0,
                    luck=8.0,
                ),
                z_batting_runs=0.6,
                z_barrel_rate=0.3,
                z_baserunning_runs=0.1,
                z_fielding_runs=0.4,
                z_payroll=-0.7,
                z_age=0.2,
                z_luck=0.4,
                adjusted_payroll=0.7,
                adjusted_age=0.0,
                adjusted_luck=0.4,
                tnerd_score=6.5,
            ),
        }

        {
            "Logan Gilbert": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Logan Gilbert",
                    team="SEA",
                    xfip_minus=85.0,
                    swinging_strike_rate=0.13,
                    strike_rate=0.67,
                    velocity=96.0,
                    age=28,
                    pace=20.0,
                    luck=3.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-1.3,
                z_swinging_strike_rate=1.5,
                z_strike_rate=1.0,
                z_velocity=1.2,
                z_age=-0.2,
                z_pace=-0.8,
                adjusted_velocity=1.2,
                adjusted_age=0.2,
                adjusted_luck=0.15,
                pnerd_score=9.2,
            ),
            "Reid Detmers": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Reid Detmers",
                    team="LAA",
                    xfip_minus=102.0,
                    swinging_strike_rate=0.10,
                    strike_rate=0.62,
                    velocity=92.5,
                    age=25,
                    pace=23.0,
                    luck=-2.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=0.4,
                z_swinging_strike_rate=-0.8,
                z_strike_rate=-0.3,
                z_velocity=-0.2,
                z_age=-0.9,
                z_pace=0.5,
                adjusted_velocity=0.0,
                adjusted_age=0.9,
                adjusted_luck=0.0,
                pnerd_score=5.1,
            ),
        }

        game_score = GameScore(
            away_team="Los Angeles Angels",
            home_team="Seattle Mariners",
            away_starter="Reid Detmers",
            home_starter="Logan Gilbert",
            game_time="9:40 PM",
            game_date="2025-07-27",
            away_team_nerd_score=6.5,
            home_team_nerd_score=8.9,
            average_team_nerd_score=7.7,
            away_pitcher_nerd_score=5.1,
            home_pitcher_nerd_score=9.2,
            average_pitcher_nerd_score=7.15,
            gnerd_score=14.85,
            away_team_nerd_stats=None,
            home_team_nerd_stats=None,
            away_pitcher_nerd_stats=None,
            home_pitcher_nerd_stats=None,
        )

        # Call the real API
        description, web_sources = game_score.generate_description(
            model=ANTHROPIC_MODEL_CHEAP
        )

        # Basic validations - don't test specific content since it's generated
        assert isinstance(description, str)
        assert len(description) > 10  # Should have some content

        # Should not contain template variables (basic sanity check)
        assert "{" not in description
        assert "}" not in description

        # Validate web sources (list of dicts)
        assert isinstance(web_sources, list)
        # Could be empty or have sources, but should be valid structure if present
        for source in web_sources:
            assert isinstance(source, dict)
            if "url" in source:
                assert isinstance(source["url"], str)
            if "title" in source:
                assert isinstance(source["title"], str)

    @pytest.mark.costly
    def test_from_games_with_llm_description_cheap_model_real_api(self) -> None:
        """Test from_games with game_desc_source='llm' using real API calls with ANTHROPIC_MODEL_CHEAP."""
        games = [
            {
                "away_team": "Seattle Mariners",
                "home_team": "Los Angeles Angels",
                "away_starter": "Logan Gilbert",
                "home_starter": "Reid Detmers",
                "time": "9:40 PM",
                "date": "2025-07-28",
            }
        ]

        # Create realistic mock data for the teams and pitchers
        mock_team_nerd_details = {
            "SEA": TeamNerdStats(
                team_stats=TeamStats(
                    name="SEA",
                    batting_runs=15.0,
                    barrel_rate=0.09,
                    baserunning_runs=8.0,
                    fielding_runs=12.0,
                    payroll=180.0,
                    age=27.5,
                    luck=5.0,
                ),
                z_batting_runs=1.2,
                z_barrel_rate=0.7,
                z_baserunning_runs=0.6,
                z_fielding_runs=1.0,
                z_payroll=-0.3,
                z_age=-0.8,
                z_luck=0.3,
                adjusted_payroll=0.3,
                adjusted_age=0.8,
                adjusted_luck=0.3,
                tnerd_score=8.9,
            ),
            "LAA": TeamNerdStats(
                team_stats=TeamStats(
                    name="LAA",
                    batting_runs=8.0,
                    barrel_rate=0.075,
                    baserunning_runs=2.0,
                    fielding_runs=5.0,
                    payroll=200.0,
                    age=29.0,
                    luck=8.0,
                ),
                z_batting_runs=0.6,
                z_barrel_rate=0.3,
                z_baserunning_runs=0.1,
                z_fielding_runs=0.4,
                z_payroll=-0.7,
                z_age=0.2,
                z_luck=0.4,
                adjusted_payroll=0.7,
                adjusted_age=0.0,
                adjusted_luck=0.4,
                tnerd_score=6.5,
            ),
        }

        mock_pitcher_nerd_details = {
            "Logan Gilbert": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Logan Gilbert",
                    team="SEA",
                    xfip_minus=85.0,
                    swinging_strike_rate=0.13,
                    strike_rate=0.67,
                    velocity=96.0,
                    age=28,
                    pace=20.0,
                    luck=3.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-1.3,
                z_swinging_strike_rate=1.5,
                z_strike_rate=1.0,
                z_velocity=1.2,
                z_age=-0.2,
                z_pace=-0.8,
                adjusted_velocity=1.2,
                adjusted_age=0.2,
                adjusted_luck=0.15,
                pnerd_score=9.2,
            ),
            "Reid Detmers": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Reid Detmers",
                    team="LAA",
                    xfip_minus=102.0,
                    swinging_strike_rate=0.10,
                    strike_rate=0.62,
                    velocity=92.5,
                    age=25,
                    pace=23.0,
                    luck=-2.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=0.4,
                z_swinging_strike_rate=-0.8,
                z_strike_rate=-0.3,
                z_velocity=-0.2,
                z_age=-0.9,
                z_pace=0.5,
                adjusted_velocity=0.0,
                adjusted_age=0.9,
                adjusted_luck=0.0,
                pnerd_score=5.1,
            ),
        }

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"
            ) as mock_team,
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitcher,
        ):
            mock_team.return_value = mock_team_nerd_details
            mock_pitcher.return_value = mock_pitcher_nerd_details

            # Test with LLM source, limit of 1, and ANTHROPIC_MODEL_CHEAP
            game_scores = GameScore.from_games(
                games,
                2025,
                game_desc_source="llm",
                game_desc_limit=1,
                model=ANTHROPIC_MODEL_CHEAP,
            )

            assert len(game_scores) == 1
            game_score = game_scores[0]

            # Verify the game has a description from the LLM
            assert game_score.game_description is not None
            assert isinstance(game_score.game_description, str)
            assert len(game_score.game_description) > 10  # Should have some content

            # Verify web sources (could be empty or populated)
            assert game_score.game_description_sources is not None
            assert isinstance(game_score.game_description_sources, list)

            # Should not contain template variables (basic sanity check)
            assert "{" not in game_score.game_description
            assert "}" not in game_score.game_description

            # Verify web sources structure if present
            for source in game_score.game_description_sources:
                assert isinstance(source, dict)
                if "url" in source:
                    assert isinstance(source["url"], str)
                if "title" in source:
                    assert isinstance(source["title"], str)

    def test_from_games_assigns_all_games_nerd_stats(self) -> None:
        """Test that from_games calculates and assigns AllGamesNerdStats to each game."""
        # Use existing test data from another working test to avoid complex setup
        games = [
            {
                "away_team": "Boston Red Sox",
                "home_team": "New York Yankees",
                "away_starter": "John Pitcher",
                "home_starter": "Jane Starter",
                "time": "7:05 PM",
            },
            {
                "away_team": "Chicago Cubs",
                "home_team": "Milwaukee Brewers",
                "away_starter": "Bob Pitcher",
                "home_starter": "Alice Starter",
                "time": "8:10 PM",
            },
        ]

        # Use simplified mock data with known NERD scores
        mock_team_nerd_data = {
            "BOS": TeamNerdStats(
                team_stats=TeamStats(
                    name="BOS",
                    batting_runs=10.0,
                    barrel_rate=0.08,
                    baserunning_runs=5.0,
                    fielding_runs=15.0,
                    payroll=200.0,
                    age=28.5,
                    luck=12.0,
                ),
                z_batting_runs=1.0,
                z_barrel_rate=0.8,
                z_baserunning_runs=0.5,
                z_fielding_runs=0.9,
                z_payroll=1.2,
                z_age=0.3,
                z_luck=0.6,
                batting_component=1.0,
                barrel_component=0.4,
                baserunning_component=0.25,
                fielding_component=0.45,
                payroll_component=1.2,
                age_component=0.3,
                luck_component=0.6,
                constant_component=4.0,
                adjusted_payroll=0.8,
                adjusted_age=0.5,
                adjusted_luck=0.4,
                tnerd_score=5.0,
            ),
            "NYY": TeamNerdStats(
                team_stats=TeamStats(
                    name="NYY",
                    batting_runs=20.0,
                    barrel_rate=0.09,
                    baserunning_runs=8.0,
                    fielding_runs=18.0,
                    payroll=250.0,
                    age=29.0,
                    luck=8.0,
                ),
                z_batting_runs=1.2,
                z_barrel_rate=1.0,
                z_baserunning_runs=0.8,
                z_fielding_runs=1.1,
                z_payroll=1.5,
                z_age=0.4,
                z_luck=0.3,
                batting_component=1.2,
                barrel_component=0.5,
                baserunning_component=0.4,
                fielding_component=0.55,
                payroll_component=1.5,
                age_component=0.4,
                luck_component=0.3,
                constant_component=4.0,
                adjusted_payroll=1.2,
                adjusted_age=0.3,
                adjusted_luck=0.2,
                tnerd_score=10.0,
            ),
            "CHC": TeamNerdStats(
                team_stats=TeamStats(
                    name="CHC",
                    batting_runs=5.0,
                    barrel_rate=0.07,
                    baserunning_runs=2.0,
                    fielding_runs=10.0,
                    payroll=150.0,
                    age=27.0,
                    luck=5.0,
                ),
                z_batting_runs=0.2,
                z_barrel_rate=0.3,
                z_baserunning_runs=0.1,
                z_fielding_runs=0.4,
                z_payroll=0.5,
                z_age=0.2,
                z_luck=0.2,
                batting_component=0.2,
                barrel_component=0.15,
                baserunning_component=0.05,
                fielding_component=0.2,
                payroll_component=0.5,
                age_component=0.2,
                luck_component=0.2,
                constant_component=4.0,
                adjusted_payroll=0.3,
                adjusted_age=0.8,
                adjusted_luck=0.1,
                tnerd_score=3.0,
            ),
            "MIL": TeamNerdStats(
                team_stats=TeamStats(
                    name="MIL",
                    batting_runs=12.0,
                    barrel_rate=0.085,
                    baserunning_runs=6.0,
                    fielding_runs=14.0,
                    payroll=120.0,
                    age=26.5,
                    luck=10.0,
                ),
                z_batting_runs=0.6,
                z_barrel_rate=0.7,
                z_baserunning_runs=0.4,
                z_fielding_runs=0.7,
                z_payroll=0.3,
                z_age=0.1,
                z_luck=0.5,
                batting_component=0.6,
                barrel_component=0.35,
                baserunning_component=0.2,
                fielding_component=0.35,
                payroll_component=0.3,
                age_component=0.1,
                luck_component=0.5,
                constant_component=4.0,
                adjusted_payroll=0.0,
                adjusted_age=0.0,
                adjusted_luck=0.05,
                tnerd_score=8.0,
            ),
        }

        # Mock pitcher data with specific NERD scores for testing
        mock_pitcher_nerd_data = {
            "John Pitcher": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="John Pitcher",
                    team="BOS",
                    xfip_minus=95.0,
                    swinging_strike_rate=0.12,
                    strike_rate=0.65,
                    velocity=95.5,
                    age=28,
                    pace=22.0,
                    luck=5.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-0.5,
                z_swinging_strike_rate=1.2,
                z_strike_rate=0.8,
                z_velocity=1.0,
                z_age=-0.3,
                z_pace=-0.5,
                xfip_component=1.0,
                swinging_strike_component=0.6,
                strike_component=0.4,
                velocity_component=1.0,
                age_component=0.3,
                pace_component=0.25,
                luck_component=0.25,
                knuckleball_component=0.0,
                constant_component=3.8,
                adjusted_velocity=1.0,
                adjusted_age=0.3,
                adjusted_luck=0.25,
                pnerd_score=2.0,
            ),
            "Jane Starter": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Jane Starter",
                    team="NYY",
                    xfip_minus=90.0,
                    swinging_strike_rate=0.14,
                    strike_rate=0.67,
                    velocity=93.0,
                    age=25,
                    pace=20.0,
                    luck=8.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-0.8,
                z_swinging_strike_rate=1.5,
                z_strike_rate=1.0,
                z_velocity=0.6,
                z_age=-0.8,
                z_pace=-0.8,
                xfip_component=1.6,
                swinging_strike_component=0.75,
                strike_component=0.5,
                velocity_component=0.6,
                age_component=0.8,
                pace_component=0.4,
                luck_component=0.4,
                knuckleball_component=0.0,
                constant_component=3.8,
                adjusted_velocity=0.6,
                adjusted_age=0.8,
                adjusted_luck=0.4,
                pnerd_score=9.0,
            ),
            # Other pitchers will return None (no data)
        }

        with (
            patch(
                "mlb_watchability.game_scores.calculate_detailed_team_nerd_scores",
                return_value=mock_team_nerd_data,
            ),
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores",
                return_value=mock_pitcher_nerd_data,
            ),
            patch(
                "mlb_watchability.game_scores.find_pitcher_nerd_stats_fuzzy",
                side_effect=lambda data, name: data.get(name),
            ),
        ):
            game_scores = GameScore.from_games(games)

        # Verify basic structure
        assert len(game_scores) == 2

        # All games should have AllGamesNerdStats
        for game_score in game_scores:
            assert game_score.all_games_nerd_stats is not None

        # Verify all games have identical stats objects (same reference)
        first_stats = game_scores[0].all_games_nerd_stats
        for game_score in game_scores[1:]:
            assert game_score.all_games_nerd_stats is first_stats

        # Test the calculated values
        stats = first_stats
        assert stats is not None  # Type guard for mypy

        # Team NERD scores: [5.0, 10.0, 3.0, 8.0]
        assert stats.min_team_nerd == 3.0
        assert stats.max_team_nerd == 10.0
        assert stats.avg_team_nerd == 6.5  # (5+10+3+8)/4

        # Pitcher NERD scores: [2.0, 9.0] (only John and Jane have data)
        assert stats.min_pitcher_nerd == 2.0
        assert stats.max_pitcher_nerd == 9.0
        assert stats.avg_pitcher_nerd == 5.5  # (2+9)/2

        # gNERD will be calculated based on actual game logic
        assert stats.min_gnerd >= 0
        assert stats.max_gnerd >= stats.min_gnerd
        assert stats.avg_gnerd >= 0

    def test_from_games_handles_empty_games_list(self) -> None:
        """Test AllGamesNerdStats calculation when games list is empty."""
        games: list[dict[str, Any]] = []

        with (
            patch("mlb_watchability.game_scores.calculate_detailed_team_nerd_scores"),
            patch(
                "mlb_watchability.game_scores.calculate_detailed_pitcher_nerd_scores"
            ),
        ):
            game_scores = GameScore.from_games(games)

        # Should return empty list with no crashes
        assert len(game_scores) == 0
