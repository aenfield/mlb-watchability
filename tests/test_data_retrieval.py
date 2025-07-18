"""Tests for the data retrieval module."""

from typing import Any
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from mlb_watchability.data_retrieval import (
    get_all_pitcher_stats,
    get_all_team_stats,
    get_game_schedule,
)
from mlb_watchability.pitcher_stats import PitcherStats
from mlb_watchability.team_stats import TeamStats


# @pytest.mark.skip(reason="Disabled until I do a new non-pybaseball impl")
class TestGetGameSchedule:
    """Test cases for the get_game_schedule function."""

    def test_get_game_schedule_with_valid_date(self) -> None:
        """Test that get_game_schedule returns games for a valid date."""

        test_date = "2024-07-15"
        mock_schedule_data = [
            {
                "game_id": 123,
                "game_datetime": "2024-07-15T20:05:00Z",
                "away_name": "Los Angeles Angels",
                "home_name": "Texas Rangers",
                "away_probable_pitcher": "Tyler Anderson",
                "home_probable_pitcher": "Nathan Eovaldi",
            },
            {
                "game_id": 124,
                "game_datetime": "2024-07-15T19:10:00Z",
                "away_name": "New York Yankees",
                "home_name": "Boston Red Sox",
                "away_probable_pitcher": "Gerrit Cole",
                "home_probable_pitcher": "Brayan Bello",
            },
        ]

        expected_games = [
            {
                "date": "2024-07-15",
                "away_team": "Los Angeles Angels",
                "home_team": "Texas Rangers",
                "time": "16:05",  # 20:05 UTC -> 16:05 Eastern (July, EDT)
                "away_starter": "Tyler Anderson",
                "home_starter": "Nathan Eovaldi",
            },
            {
                "date": "2024-07-15",
                "away_team": "New York Yankees",
                "home_team": "Boston Red Sox",
                "time": "15:10",  # 19:10 UTC -> 15:10 Eastern (July, EDT)
                "away_starter": "Gerrit Cole",
                "home_starter": "Brayan Bello",
            },
        ]

        with patch(
            "mlb_watchability.data_retrieval.statsapi.schedule"
        ) as mock_schedule:
            mock_schedule.return_value = mock_schedule_data
            result = get_game_schedule(test_date)

            assert result == expected_games
            mock_schedule.assert_called_once()

    def test_get_game_schedule_with_empty_schedule(self) -> None:
        """Test that get_game_schedule returns empty list when no games scheduled."""

        test_date = "2024-12-01"  # Off-season date
        mock_empty_schedule: list[dict[str, Any]] = []

        with patch(
            "mlb_watchability.data_retrieval.statsapi.schedule"
        ) as mock_schedule:
            mock_schedule.return_value = mock_empty_schedule
            result = get_game_schedule(test_date)

            assert result == []
            mock_schedule.assert_called_once()

    def test_get_game_schedule_with_missing_starters(self) -> None:
        """Test that get_game_schedule handles missing starting pitcher data."""

        test_date = "2024-07-15"
        mock_schedule_data = [
            {
                "game_id": 123,
                "game_datetime": "2024-07-15T20:05:00Z",
                "away_name": "Los Angeles Angels",
                "home_name": "Texas Rangers",
                "away_probable_pitcher": "Tyler Anderson",
                "home_probable_pitcher": "",  # Empty string for missing pitcher
            },
        ]

        expected_games = [
            {
                "date": "2024-07-15",
                "away_team": "Los Angeles Angels",
                "home_team": "Texas Rangers",
                "time": "16:05",  # 20:05 UTC -> 16:05 Eastern (July, EDT)
                "away_starter": "Tyler Anderson",
                "home_starter": None,
            },
        ]

        with patch(
            "mlb_watchability.data_retrieval.statsapi.schedule"
        ) as mock_schedule:
            mock_schedule.return_value = mock_schedule_data
            result = get_game_schedule(test_date)

            assert result == expected_games

    def test_get_game_schedule_with_invalid_date_format(self) -> None:
        """Test that get_game_schedule raises ValueError for invalid date format."""

        invalid_date = "invalid-date"

        with pytest.raises(ValueError, match="Invalid date format"):
            get_game_schedule(invalid_date)

    def test_get_game_schedule_with_future_date(self) -> None:
        """Test that get_game_schedule handles future dates appropriately."""

        future_date = "2030-07-15"
        mock_empty_schedule: list[dict[str, Any]] = []

        with patch(
            "mlb_watchability.data_retrieval.statsapi.schedule"
        ) as mock_schedule:
            mock_schedule.return_value = mock_empty_schedule
            result = get_game_schedule(future_date)

            assert result == []

    def test_get_game_schedule_with_api_error(self) -> None:
        """Test that get_game_schedule handles API errors gracefully."""

        test_date = "2024-07-15"

        with patch(
            "mlb_watchability.data_retrieval.statsapi.schedule"
        ) as mock_schedule:
            mock_schedule.side_effect = Exception("API Error")

            with pytest.raises(RuntimeError, match="Failed to retrieve game schedule"):
                get_game_schedule(test_date)

    def test_get_game_schedule_date_parsing(self) -> None:
        """Test that get_game_schedule properly validates date format."""

        invalid_dates = [
            "2024-13-01",  # Invalid month
            "2024-02-30",  # Invalid day
            "24-07-15",  # Wrong year format
            "2024/07/15",  # Wrong separator
            "",  # Empty string
        ]

        for invalid_date in invalid_dates:
            with pytest.raises(ValueError, match="Invalid date format"):
                get_game_schedule(invalid_date)


# @pytest.mark.skip(reason="Disabled until I do a new non-pybaseball impl")
class TestGetGameScheduleIntegration:
    """Integration tests that call the real pybaseball API."""

    def test_get_game_schedule_integration_with_known_date(self) -> None:
        """Test that get_game_schedule works with real API for a known date with games."""
        # Use a known date during the 2024 season when games were played
        test_date = "2024-07-13"  # Mid-season date

        # Call the real API
        result = get_game_schedule(test_date)

        # Basic validation that we got reasonable data
        assert isinstance(result, list)

        # If games were played that day, validate the structure
        if result:
            for game in result:
                assert isinstance(game, dict)
                assert "date" in game
                assert "away_team" in game
                assert "home_team" in game
                assert "time" in game
                assert "away_starter" in game
                assert "home_starter" in game

                # Validate data types and basic format
                assert game["date"] == test_date
                assert isinstance(game["away_team"], str)
                assert isinstance(game["home_team"], str)
                assert (
                    game["time"] is not None
                )  # Time should be available in MLB-StatsAPI (Eastern time)
                # Starting pitchers can be None or string
                if game["away_starter"] is not None:
                    assert isinstance(game["away_starter"], str)
                if game["home_starter"] is not None:
                    assert isinstance(game["home_starter"], str)

                # Team names should be non-empty strings
                assert len(game["away_team"]) > 0
                assert len(game["home_team"]) > 0

    def test_get_game_schedule_integration_with_offseason_date(self) -> None:
        """Test that get_game_schedule works with real API for an off-season date."""
        # Use a known off-season date
        test_date = "2024-12-01"  # December is off-season

        # Call the real API
        result = get_game_schedule(test_date)

        # Should return empty list for off-season dates
        assert isinstance(result, list)
        assert result == []

    def test_get_game_schedule_integration_with_recent_date(self) -> None:
        """Test that get_game_schedule works with real API for a recent date."""
        # Use a date from the current season (2024) that's likely to have games
        test_date = "2024-09-15"  # September is typically active season

        # Call the real API
        result = get_game_schedule(test_date)

        # Basic validation
        assert isinstance(result, list)

        # If games were played, validate basic structure
        if result:
            # Should have multiple games on a typical day
            assert len(result) >= 1

            # Check first game structure
            game = result[0]
            assert isinstance(game, dict)
            required_keys = [
                "date",
                "away_team",
                "home_team",
                "time",
                "away_starter",
                "home_starter",
            ]
            for key in required_keys:
                assert key in game

            # Date should match what we requested
            assert game["date"] == test_date


class TestGetAllPitcherStats:
    """Test cases for the get_all_pitcher_stats function."""

    def test_get_all_pitcher_stats_with_valid_data(self) -> None:
        """Test that get_all_pitcher_stats returns statistics for all starting pitchers."""

        # Mock data for pybaseball.pitching_stats
        mock_pitcher_data = pd.DataFrame(
            {
                "Name": [
                    "Tarik Skubal",
                    "Matt Waldron",
                    "Gerrit Cole",
                    "Spencer Strider",
                ],
                "Team": ["DET", "SD", "NYY", "ATL"],
                "GS": [25, 20, 30, 28],
                "IP": [150.0, 120.0, 180.0, 165.0],
                "xFIP-": [85, 105, 90, 80],
                "SwStr%": [0.12, 0.09, 0.11, 0.15],
                "Strikes": [1200, 950, 1350, 1280],
                "Pitches": [2000, 1600, 2200, 2100],
                "FBv": [94.5, 89.2, 96.1, 98.5],
                "Age": [27, 26, 33, 25],
                "Pace": [22.5, 25.1, 20.8, 19.2],
                "ERA-": [75, 110, 85, 70],
                "KN%": [0.0, 0.0, 0.0, 0.0],
            }
        )

        with patch(
            "mlb_watchability.data_retrieval.pb.pitching_stats"
        ) as mock_pitching_stats:
            mock_pitching_stats.return_value = mock_pitcher_data

            result = get_all_pitcher_stats(season=2024)

            # Should return stats for all pitchers
            assert len(result) == 4
            assert "Tarik Skubal" in result
            assert "Matt Waldron" in result
            assert "Gerrit Cole" in result
            assert "Spencer Strider" in result

            # Verify Tarik Skubal stats
            skubal_stats = result["Tarik Skubal"]
            assert isinstance(skubal_stats, PitcherStats)
            assert skubal_stats.name == "Tarik Skubal"
            assert skubal_stats.team == "DET"
            assert skubal_stats.xfip_minus == 85
            assert skubal_stats.swinging_strike_rate == 0.12
            assert skubal_stats.strike_rate == 0.6  # 1200/2000
            assert skubal_stats.velocity == 94.5
            assert skubal_stats.age == 27
            assert skubal_stats.pace == 22.5
            assert skubal_stats.luck == -10.0  # 75 - 85
            assert skubal_stats.knuckleball_rate == 0.0

            # Verify Matt Waldron stats
            waldron_stats = result["Matt Waldron"]
            assert isinstance(waldron_stats, PitcherStats)
            assert waldron_stats.name == "Matt Waldron"
            assert waldron_stats.team == "SD"
            assert waldron_stats.strike_rate == 0.59375  # 950/1600
            assert waldron_stats.luck == 5.0  # 110 - 105

            mock_pitching_stats.assert_called_once_with(2024, qual=20)

    def test_get_all_pitcher_stats_with_knuckleball_nan(self) -> None:
        """Test that get_all_pitcher_stats handles NaN KN% values correctly."""

        # Mock data with NaN KN% values
        mock_pitcher_data = pd.DataFrame(
            {
                "Name": ["Test Pitcher"],
                "Team": ["TEST"],
                "GS": [25],
                "IP": [150.0],
                "xFIP-": [100],
                "SwStr%": [0.10],
                "Strikes": [1000],
                "Pitches": [1800],
                "FBv": [92.0],
                "Age": [28],
                "Pace": [23.0],
                "ERA-": [95],
                "KN%": [float("nan")],  # NaN value
            }
        )

        with patch(
            "mlb_watchability.data_retrieval.pb.pitching_stats"
        ) as mock_pitching_stats:
            mock_pitching_stats.return_value = mock_pitcher_data

            result = get_all_pitcher_stats(season=2024)

            # Should handle NaN KN% by setting to 0
            assert len(result) == 1
            pitcher_stats = result["Test Pitcher"]
            assert pitcher_stats.knuckleball_rate == 0.0

    def test_get_all_pitcher_stats_with_no_starting_pitchers(self) -> None:
        """Test that get_all_pitcher_stats handles data with no starting pitchers."""

        # Mock data with pitchers that have 0 games started
        mock_pitcher_data = pd.DataFrame(
            {
                "Name": ["Relief Pitcher"],
                "Team": ["TEST"],
                "GS": [0],  # No games started
                "IP": [50.0],
                "xFIP-": [100],
                "SwStr%": [0.10],
                "Strikes": [400],
                "Pitches": [700],
                "FBv": [92.0],
                "Age": [28],
                "Pace": [20.0],
                "ERA-": [95],
                "KN%": [0.0],
            }
        )

        with patch(
            "mlb_watchability.data_retrieval.pb.pitching_stats"
        ) as mock_pitching_stats:
            mock_pitching_stats.return_value = mock_pitcher_data

            result = get_all_pitcher_stats(season=2024)

            # Should return empty dict since no starting pitchers
            assert len(result) == 0

    def test_get_all_pitcher_stats_with_api_error(self) -> None:
        """Test that get_all_pitcher_stats handles API errors gracefully."""

        with patch(
            "mlb_watchability.data_retrieval.pb.pitching_stats"
        ) as mock_pitching_stats:
            mock_pitching_stats.side_effect = Exception("API Error")

            with pytest.raises(
                RuntimeError, match="Failed to retrieve pitcher statistics"
            ):
                get_all_pitcher_stats(season=2024)

    def test_get_all_pitcher_stats_with_different_season(self) -> None:
        """Test that get_all_pitcher_stats works with different seasons."""

        # Mock data
        mock_pitcher_data = pd.DataFrame(
            {
                "Name": ["Historic Pitcher"],
                "Team": ["OLD"],
                "GS": [30],
                "IP": [200.0],
                "xFIP-": [95],
                "SwStr%": [0.08],
                "Strikes": [1500],
                "Pitches": [2500],
                "FBv": [90.0],
                "Age": [30],
                "Pace": [25.0],
                "ERA-": [100],
                "KN%": [0.0],
            }
        )

        with patch(
            "mlb_watchability.data_retrieval.pb.pitching_stats"
        ) as mock_pitching_stats:
            mock_pitching_stats.return_value = mock_pitcher_data

            result = get_all_pitcher_stats(season=2023)

            # Should call with the correct season
            assert len(result) == 1
            mock_pitching_stats.assert_called_once_with(2023, qual=20)


class TestGetAllPitcherStatsIntegration:
    """Integration tests that call the real pybaseball API."""

    def test_get_all_pitcher_stats_integration_with_real_data(self) -> None:
        """Test that get_all_pitcher_stats works with real API data."""

        # Call the real API
        result = get_all_pitcher_stats(season=2024)

        # Basic validation that we got reasonable data
        assert isinstance(result, dict)

        # We should get multiple pitchers (depends on season timing)
        if result:
            # Should have multiple starting pitchers
            assert len(result) >= 10  # At least 10 starting pitchers in a season

            # Check a few random pitchers
            for _, pitcher_stats in list(result.items())[:5]:
                assert isinstance(pitcher_stats, PitcherStats)
                assert pitcher_stats.name
                assert pitcher_stats.team

                # Validate data types and reasonable ranges
                assert isinstance(
                    pitcher_stats.xfip_minus, int | float | np.integer | np.floating
                )
                assert 0 <= pitcher_stats.xfip_minus <= 300

                assert isinstance(
                    pitcher_stats.swinging_strike_rate, float | np.floating
                )
                assert 0.0 <= pitcher_stats.swinging_strike_rate <= 1.0

                assert isinstance(pitcher_stats.strike_rate, float | np.floating)
                assert 0.0 <= pitcher_stats.strike_rate <= 1.0

                assert isinstance(
                    pitcher_stats.velocity, int | float | np.integer | np.floating
                )
                assert 70.0 <= pitcher_stats.velocity <= 110.0

                assert isinstance(pitcher_stats.age, int | np.integer)
                assert 18 <= pitcher_stats.age <= 50


class TestGetAllTeamStats:
    """Test cases for the get_all_team_stats function."""

    def test_get_all_team_stats_with_valid_data(self) -> None:
        """Test that get_all_team_stats returns statistics for all teams."""

        # Mock data for pybaseball.team_batting
        mock_team_batting_data = pd.DataFrame(
            {
                "Team": ["LAD", "NYY", "ATL", "HOU"],
                "Bat": [45.2, 38.1, 41.7, 39.3],
                "Barrel%": [0.089, 0.076, 0.081, 0.083],
                "BsR": [8.2, -2.1, 3.5, 5.8],
                "Fld": [12.3, -8.4, 15.2, 6.7],
                "wRC": [720, 680, 695, 710],
                "R": [698, 695, 675, 702],
            }
        )

        # Mock payroll data
        mock_payroll_data = pd.DataFrame(
            {
                "Team": ["LAD", "NYY", "ATL", "HOU"],
                "Age": [29.2, 30.1, 28.5, 29.8],
                "Payroll": [341038001, 290905867, 175000000, 220000000],
            }
        )

        with (
            patch(
                "mlb_watchability.data_retrieval.pb.team_batting"
            ) as mock_team_batting,
            patch("mlb_watchability.data_retrieval.pd.read_csv") as mock_read_csv,
        ):
            mock_team_batting.return_value = mock_team_batting_data
            mock_read_csv.return_value = mock_payroll_data

            result = get_all_team_stats(season=2025)

            # Should return stats for all teams
            assert len(result) == 4
            assert "LAD" in result
            assert "NYY" in result
            assert "ATL" in result
            assert "HOU" in result

            # Verify LAD stats
            lad_stats = result["LAD"]
            assert isinstance(lad_stats, TeamStats)
            assert lad_stats.name == "LAD"
            assert lad_stats.batting_runs == 45.2
            assert lad_stats.barrel_rate == 0.089
            assert lad_stats.baserunning_runs == 8.2
            assert lad_stats.fielding_runs == 12.3
            assert lad_stats.payroll == 341.038001  # Converted to millions
            assert lad_stats.age == 29.2
            assert lad_stats.luck == 22.0  # wRC (720) - R (698)

            # Verify NYY stats
            nyy_stats = result["NYY"]
            assert isinstance(nyy_stats, TeamStats)
            assert nyy_stats.name == "NYY"
            assert nyy_stats.luck == -15.0  # wRC (680) - R (695)

            mock_team_batting.assert_called_once_with(2025)
            mock_read_csv.assert_called_once_with("data/payroll-spotrac.2025.csv")

    def test_get_all_team_stats_with_team_mapping(self) -> None:
        """Test that get_all_team_stats handles team name mapping correctly."""

        # Mock data with teams that need mapping
        mock_team_batting_data = pd.DataFrame(
            {
                "Team": ["TBR", "WSN", "SDP", "SFG", "KCR"],
                "Bat": [25.0, 20.0, 30.0, 35.0, 15.0],
                "Barrel%": [0.070, 0.065, 0.075, 0.080, 0.060],
                "BsR": [5.0, 2.0, 8.0, 12.0, -3.0],
                "Fld": [8.0, -5.0, 10.0, 15.0, -12.0],
                "wRC": [600, 580, 650, 680, 550],
                "R": [590, 585, 640, 675, 560],
            }
        )

        # Mock payroll data with original team names
        mock_payroll_data = pd.DataFrame(
            {
                "Team": ["TB", "WSH", "SD", "SF", "KC"],
                "Age": [27.5, 30.2, 28.8, 29.1, 31.0],
                "Payroll": [100000000, 150000000, 209327115, 195326431, 120000000],
            }
        )

        with (
            patch(
                "mlb_watchability.data_retrieval.pb.team_batting"
            ) as mock_team_batting,
            patch("mlb_watchability.data_retrieval.pd.read_csv") as mock_read_csv,
        ):
            mock_team_batting.return_value = mock_team_batting_data
            mock_read_csv.return_value = mock_payroll_data

            result = get_all_team_stats(season=2025)

            # Should return stats for all teams after mapping
            assert len(result) == 5
            assert "TBR" in result
            assert "WSN" in result
            assert "SDP" in result
            assert "SFG" in result
            assert "KCR" in result

            # Verify team mapping worked correctly
            tbr_stats = result["TBR"]
            assert tbr_stats.name == "TBR"
            assert tbr_stats.age == 27.5  # Original TB age
            assert tbr_stats.payroll == 100.0  # Original TB payroll in millions

    def test_get_all_team_stats_with_missing_columns(self) -> None:
        """Test that get_all_team_stats handles missing required columns."""

        # Mock data missing required columns
        mock_team_batting_data = pd.DataFrame(
            {
                "Team": ["LAD"],
                "Bat": [45.2],
                # Missing Barrel%, BsR, Fld, wRC, R
            }
        )

        mock_payroll_data = pd.DataFrame(
            {
                "Team": ["LAD"],
                "Age": [29.2],
                "Payroll": [341038001],
            }
        )

        with (
            patch(
                "mlb_watchability.data_retrieval.pb.team_batting"
            ) as mock_team_batting,
            patch("mlb_watchability.data_retrieval.pd.read_csv") as mock_read_csv,
        ):
            mock_team_batting.return_value = mock_team_batting_data
            mock_read_csv.return_value = mock_payroll_data

            with pytest.raises(RuntimeError, match="Missing required columns"):
                get_all_team_stats(season=2025)

    def test_get_all_team_stats_with_missing_barrel_rate(self) -> None:
        """Test that get_all_team_stats handles missing Barrel% values."""

        # Mock data with NaN Barrel% values
        mock_team_batting_data = pd.DataFrame(
            {
                "Team": ["TEST"],
                "Bat": [25.0],
                "Barrel%": [float("nan")],  # NaN value
                "BsR": [5.0],
                "Fld": [8.0],
                "wRC": [600],
                "R": [590],
            }
        )

        mock_payroll_data = pd.DataFrame(
            {
                "Team": ["TEST"],
                "Age": [28.0],
                "Payroll": [150000000],
            }
        )

        with (
            patch(
                "mlb_watchability.data_retrieval.pb.team_batting"
            ) as mock_team_batting,
            patch("mlb_watchability.data_retrieval.pd.read_csv") as mock_read_csv,
        ):
            mock_team_batting.return_value = mock_team_batting_data
            mock_read_csv.return_value = mock_payroll_data

            result = get_all_team_stats(season=2025)

            # Should handle NaN Barrel% by setting to 0
            assert len(result) == 1
            team_stats = result["TEST"]
            assert team_stats.barrel_rate == 0.0

    def test_get_all_team_stats_with_percentage_conversion(self) -> None:
        """Test that get_all_team_stats handles percentage conversion correctly."""

        # Mock data with percentage values > 1.0
        mock_team_batting_data = pd.DataFrame(
            {
                "Team": ["TEST"],
                "Bat": [25.0],
                "Barrel%": [8.9],  # Percentage format (should be converted to 0.089)
                "BsR": [5.0],
                "Fld": [8.0],
                "wRC": [600],
                "R": [590],
            }
        )

        mock_payroll_data = pd.DataFrame(
            {
                "Team": ["TEST"],
                "Age": [28.0],
                "Payroll": [150000000],
            }
        )

        with (
            patch(
                "mlb_watchability.data_retrieval.pb.team_batting"
            ) as mock_team_batting,
            patch("mlb_watchability.data_retrieval.pd.read_csv") as mock_read_csv,
        ):
            mock_team_batting.return_value = mock_team_batting_data
            mock_read_csv.return_value = mock_payroll_data

            result = get_all_team_stats(season=2025)

            # Should convert percentage to decimal
            assert len(result) == 1
            team_stats = result["TEST"]
            assert abs(team_stats.barrel_rate - 0.089) < 0.0001

    def test_get_all_team_stats_with_api_error(self) -> None:
        """Test that get_all_team_stats handles API errors gracefully."""

        with patch(
            "mlb_watchability.data_retrieval.pb.team_batting"
        ) as mock_team_batting:
            mock_team_batting.side_effect = Exception("API Error")

            with pytest.raises(
                RuntimeError, match="Failed to retrieve team statistics"
            ):
                get_all_team_stats(season=2025)

    def test_get_all_team_stats_with_csv_error(self) -> None:
        """Test that get_all_team_stats handles CSV read errors gracefully."""

        mock_team_batting_data = pd.DataFrame(
            {
                "Team": ["LAD"],
                "Bat": [45.2],
                "Barrel%": [0.089],
                "BsR": [8.2],
                "Fld": [12.3],
                "wRC": [720],
                "R": [698],
            }
        )

        with (
            patch(
                "mlb_watchability.data_retrieval.pb.team_batting"
            ) as mock_team_batting,
            patch("mlb_watchability.data_retrieval.pd.read_csv") as mock_read_csv,
        ):
            mock_team_batting.return_value = mock_team_batting_data
            mock_read_csv.side_effect = Exception("CSV Error")

            with pytest.raises(
                RuntimeError, match="Failed to retrieve team statistics"
            ):
                get_all_team_stats(season=2025)

    def test_get_all_team_stats_with_different_season(self) -> None:
        """Test that get_all_team_stats works with different seasons."""

        mock_team_batting_data = pd.DataFrame(
            {
                "Team": ["HISTORIC"],
                "Bat": [30.0],
                "Barrel%": [0.070],
                "BsR": [5.0],
                "Fld": [10.0],
                "wRC": [650],
                "R": [640],
            }
        )

        mock_payroll_data = pd.DataFrame(
            {
                "Team": ["HISTORIC"],
                "Age": [28.5],
                "Payroll": [180000000],
            }
        )

        with (
            patch(
                "mlb_watchability.data_retrieval.pb.team_batting"
            ) as mock_team_batting,
            patch("mlb_watchability.data_retrieval.pd.read_csv") as mock_read_csv,
        ):
            mock_team_batting.return_value = mock_team_batting_data
            mock_read_csv.return_value = mock_payroll_data

            result = get_all_team_stats(season=2024)

            # Should call with the correct season
            assert len(result) == 1
            mock_team_batting.assert_called_once_with(2024)


class TestGetAllTeamStatsIntegration:
    """Integration tests that call the real pybaseball API."""

    def test_get_all_team_stats_integration_with_real_data(self) -> None:
        """Test that get_all_team_stats works with real API data."""

        # Call the real API
        result = get_all_team_stats(season=2025)

        # Basic validation that we got reasonable data
        assert isinstance(result, dict)

        # We should get 30 teams
        if result:
            assert (
                len(result) >= 20
            )  # At least 20 teams (allowing for some missing data)

            # Check a few random teams
            for team_name, team_stats in list(result.items())[:5]:
                assert isinstance(team_stats, TeamStats)
                assert team_stats.name == team_name
                assert team_stats.name  # Should have a team name

                # Validate data types and reasonable ranges
                assert isinstance(
                    team_stats.batting_runs, int | float | np.integer | np.floating
                )
                assert -200.0 <= team_stats.batting_runs <= 200.0

                assert isinstance(team_stats.barrel_rate, float | np.floating)
                assert 0.0 <= team_stats.barrel_rate <= 0.20

                assert isinstance(
                    team_stats.baserunning_runs, int | float | np.integer | np.floating
                )
                assert -50.0 <= team_stats.baserunning_runs <= 50.0

                assert isinstance(
                    team_stats.fielding_runs, int | float | np.integer | np.floating
                )
                assert -100.0 <= team_stats.fielding_runs <= 100.0

                assert isinstance(
                    team_stats.payroll, int | float | np.integer | np.floating
                )
                assert 30.0 <= team_stats.payroll <= 500.0

                assert isinstance(
                    team_stats.age, int | float | np.integer | np.floating
                )
                assert 20.0 <= team_stats.age <= 40.0

                assert isinstance(
                    team_stats.luck, int | float | np.integer | np.floating
                )
                assert -100.0 <= team_stats.luck <= 100.0

    def test_get_all_team_stats_integration_with_previous_season(self) -> None:
        """Test that get_all_team_stats works with previous season data."""

        # Call the real API for 2024 season
        result = get_all_team_stats(season=2024)

        # Basic validation
        assert isinstance(result, dict)

        # Should have multiple teams from 2024
        if result:
            assert len(result) >= 20  # At least 20 teams from 2024

            # Validate some of the data
            for team_name, team_stats in list(result.items())[:3]:
                assert isinstance(team_stats, TeamStats)
                assert team_stats.name == team_name
                assert team_stats.name  # Should have a team name

                # Validate reasonable statistics
                assert isinstance(
                    team_stats.batting_runs, int | float | np.integer | np.floating
                )
                assert -200.0 <= team_stats.batting_runs <= 200.0

                assert isinstance(team_stats.barrel_rate, float | np.floating)
                assert 0.0 <= team_stats.barrel_rate <= 0.20

                assert isinstance(
                    team_stats.payroll, int | float | np.integer | np.floating
                )
                assert 30.0 <= team_stats.payroll <= 500.0

                assert isinstance(
                    team_stats.age, int | float | np.integer | np.floating
                )
                assert 20.0 <= team_stats.age <= 40.0

                assert isinstance(
                    team_stats.luck, int | float | np.integer | np.floating
                )
                assert -100.0 <= team_stats.luck <= 100.0

    def test_get_all_pitcher_stats_integration_with_previous_season(self) -> None:
        """Test that get_all_pitcher_stats works with previous season data."""

        # Call the real API for 2023 season
        result = get_all_pitcher_stats(season=2023)

        # Basic validation
        assert isinstance(result, dict)

        # Should have multiple starting pitchers from 2023
        if result:
            assert len(result) >= 10  # At least 10 starting pitchers in 2023

            # Validate some of the data
            for pitcher_name, pitcher_stats in list(result.items())[:3]:
                assert isinstance(pitcher_stats, PitcherStats)
                assert pitcher_stats.name == pitcher_name
                assert pitcher_stats.team  # Should have a team

                # Validate reasonable statistics
                assert isinstance(
                    pitcher_stats.velocity, int | float | np.integer | np.floating
                )
                assert 70.0 <= pitcher_stats.velocity <= 110.0

                assert isinstance(pitcher_stats.age, int | np.integer)
                assert 18 <= pitcher_stats.age <= 50
