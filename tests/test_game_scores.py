"""Tests for game score calculator."""

from unittest.mock import patch

import pytest

from mlb_watchability.game_scores import GameScore, calculate_game_scores
from mlb_watchability.pitcher_stats import PitcherNerdStats, PitcherStats
from mlb_watchability.team_stats import TeamNerdStats, TeamStats


class TestGameScores:
    """Test cases for game score calculations."""

    def test_calculate_game_scores_with_both_pitchers(self) -> None:
        """Test gNERD calculation when both starting pitchers have data."""
        # Mock game data
        games = [
            {
                "away_team": "Boston Red Sox",
                "home_team": "New York Yankees",
                "away_starter": "John Pitcher",
                "home_starter": "Jane Starter",
                "time": "7:05 PM",
            }
        ]

        # Mock team NERD data
        mock_team_nerd_details = {
            "BOS": TeamNerdStats(
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
            ),
            "NYY": TeamNerdStats(
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
            ),
        }

        # Mock pitcher NERD data
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

            game_scores = calculate_game_scores(games, 2025)

            assert len(game_scores) == 1
            game_score = game_scores[0]

            assert game_score.away_team == "Boston Red Sox"
            assert game_score.home_team == "New York Yankees"
            assert game_score.away_starter == "John Pitcher"
            assert game_score.home_starter == "Jane Starter"
            assert game_score.game_time == "7:05 PM"

            # Check team NERD scores
            assert game_score.away_team_nerd == 8.2
            assert game_score.home_team_nerd == 9.5
            assert game_score.average_team_nerd == pytest.approx((8.2 + 9.5) / 2)

            # Check pitcher NERD scores
            assert game_score.away_pitcher_nerd == 6.8
            assert game_score.home_pitcher_nerd == 7.5
            assert game_score.average_pitcher_nerd == pytest.approx((6.8 + 7.5) / 2)

            # Check final gNERD score = average team NERD + average pitcher NERD
            expected_gnerd = ((8.2 + 9.5) / 2) + ((6.8 + 7.5) / 2)
            assert game_score.gnerd_score == pytest.approx(expected_gnerd)

    def test_calculate_game_scores_with_one_pitcher(self) -> None:
        """Test gNERD calculation when only one starting pitcher has data."""
        games = [
            {
                "away_team": "Chicago Cubs",
                "home_team": "Milwaukee Brewers",
                "away_starter": "Known Pitcher",
                "home_starter": "TBD",
                "time": "2:20 PM",
            }
        ]

        mock_team_nerd_details = {
            "CHC": TeamNerdStats(
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
            ),
            "MIL": TeamNerdStats(
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
            ),
        }

        mock_pitcher_nerd_details = {
            "Known Pitcher": PitcherNerdStats(
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

            game_scores = calculate_game_scores(games, 2025)

            assert len(game_scores) == 1
            game_score = game_scores[0]

            # Check team scores
            assert game_score.away_team_nerd == 6.8
            assert game_score.home_team_nerd == 7.9
            assert game_score.average_team_nerd == pytest.approx((6.8 + 7.9) / 2)

            # Check pitcher scores - only one available
            assert game_score.away_pitcher_nerd == 5.5
            assert game_score.home_pitcher_nerd is None
            assert game_score.average_pitcher_nerd == 5.5  # Only one pitcher available

            # Check final gNERD score
            expected_gnerd = ((6.8 + 7.9) / 2) + 5.5
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

            game_scores = calculate_game_scores(games, 2025)

            assert len(game_scores) == 1
            game_score = game_scores[0]

            # Check team scores
            assert game_score.away_team_nerd == 5.95
            assert game_score.home_team_nerd == 11.4
            assert game_score.average_team_nerd == pytest.approx((5.95 + 11.4) / 2)

            # Check pitcher scores - none available
            assert game_score.away_pitcher_nerd is None
            assert game_score.home_pitcher_nerd is None
            assert game_score.average_pitcher_nerd is None

            # Check final gNERD score - only team NERD since no pitcher data
            expected_gnerd = (5.95 + 11.4) / 2
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

            game_scores = calculate_game_scores(games, 2025)

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
        game_score = GameScore(
            away_team="Team A",
            home_team="Team B",
            away_starter="Pitcher A",
            home_starter="Pitcher B",
            game_time="7:00 PM",
            away_team_nerd=5.0,
            home_team_nerd=6.0,
            average_team_nerd=5.5,
            away_pitcher_nerd=7.0,
            home_pitcher_nerd=8.0,
            average_pitcher_nerd=7.5,
            gnerd_score=13.0,
        )

        assert game_score.away_team == "Team A"
        assert game_score.home_team == "Team B"
        assert game_score.away_starter == "Pitcher A"
        assert game_score.home_starter == "Pitcher B"
        assert game_score.game_time == "7:00 PM"
        assert game_score.away_team_nerd == 5.0
        assert game_score.home_team_nerd == 6.0
        assert game_score.average_team_nerd == 5.5
        assert game_score.away_pitcher_nerd == 7.0
        assert game_score.home_pitcher_nerd == 8.0
        assert game_score.average_pitcher_nerd == 7.5
        assert game_score.gnerd_score == 13.0
