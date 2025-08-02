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
                "time": "13:05",  # 20:05 UTC -> 13:05 Pacific (July, PDT)
                "away_starter": "Tyler Anderson",
                "home_starter": "Nathan Eovaldi",
            },
            {
                "date": "2024-07-15",
                "away_team": "New York Yankees",
                "home_team": "Boston Red Sox",
                "time": "12:10",  # 19:10 UTC -> 12:10 Pacific (July, PDT)
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
                "time": "13:05",  # 20:05 UTC -> 13:05 Pacific (July, PDT)
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


@pytest.mark.costly
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
            assert isinstance(skubal_stats, dict)
            assert skubal_stats["Name"] == "Tarik Skubal"
            assert skubal_stats["Team"] == "DET"
            assert skubal_stats["xFIP-"] == 85
            assert skubal_stats["SwStr%"] == 0.12
            assert skubal_stats["Strike_Rate"] == 0.6  # 1200/2000
            assert skubal_stats["FBv"] == 94.5
            assert skubal_stats["Age"] == 27
            assert skubal_stats["Pace"] == 22.5
            assert skubal_stats["Luck"] == -10.0  # 75 - 85
            assert skubal_stats["KN%"] == 0.0

            # Verify Matt Waldron stats
            waldron_stats = result["Matt Waldron"]
            assert isinstance(waldron_stats, dict)
            assert waldron_stats["Name"] == "Matt Waldron"
            assert waldron_stats["Team"] == "SD"
            assert waldron_stats["Strike_Rate"] == 0.59375  # 950/1600
            assert waldron_stats["Luck"] == 5.0  # 110 - 105

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
            assert pitcher_stats["KN%"] == 0.0

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


@pytest.mark.costly
class TestGetAllPitcherStatsIntegration:
    """Integration tests that call the real pybaseball API."""

    def test_get_all_pitcher_stats_integration_with_real_data(self) -> None:
        """Test that get_all_pitcher_stats works with real API data."""

        # Call the real API
        result = get_all_pitcher_stats(season=2025)

        # Basic validation that we got reasonable data
        assert isinstance(result, dict)

        # We should get multiple pitchers (depends on season timing)
        if result:
            # Should have multiple starting pitchers
            assert len(result) >= 10  # At least 10 starting pitchers in a season

            # Check a few random pitchers
            for _, pitcher_stats in list(result.items())[:5]:
                assert isinstance(pitcher_stats, dict)
                assert pitcher_stats["Name"]
                assert pitcher_stats["Team"]

                # Validate data types and reasonable ranges
                assert isinstance(
                    pitcher_stats["xFIP-"], int | float | np.integer | np.floating
                )
                assert 0 <= pitcher_stats["xFIP-"] <= 300

                assert isinstance(pitcher_stats["SwStr%"], float | np.floating)
                assert 0.0 <= pitcher_stats["SwStr%"] <= 1.0

                assert isinstance(pitcher_stats["Strike_Rate"], float | np.floating)
                assert 0.0 <= pitcher_stats["Strike_Rate"] <= 1.0

                assert isinstance(
                    pitcher_stats["FBv"], int | float | np.integer | np.floating
                )
                assert 70.0 <= pitcher_stats["FBv"] <= 110.0

                assert isinstance(pitcher_stats["Age"], int | np.integer)
                assert 18 <= pitcher_stats["Age"] <= 50


@pytest.mark.costly
class TestGetAllTeamStatsIntegration:
    """Integration tests that call the real pybaseball API."""

    def test_get_all_team_stats_integration_with_real_data(self) -> None:
        """Test that get_all_team_stats works with real API data."""

        # Call the real API
        result = get_all_team_stats(season=2025)

        # Basic validation that we got reasonable data
        assert isinstance(result, dict)

        # We should get multiple teams (30 MLB teams)
        if result:
            # Should have multiple teams
            assert len(result) >= 10  # At least 10 teams in a season

            # Check a few random teams
            for _, team_stats in list(result.items())[:5]:
                assert isinstance(team_stats, dict)
                assert team_stats["Team"]

                # Validate data types and reasonable ranges
                assert isinstance(
                    team_stats["Bat"], int | float | np.integer | np.floating
                )
                assert -200 <= team_stats["Bat"] <= 200  # Batting runs

                assert isinstance(team_stats["Barrel%"], float | np.floating)
                assert 0.0 <= team_stats["Barrel%"] <= 1.0  # Barrel rate as decimal

                assert isinstance(
                    team_stats["BsR"], int | float | np.integer | np.floating
                )
                assert -50 <= team_stats["BsR"] <= 50  # Baserunning runs

                assert isinstance(
                    team_stats["Fld"], int | float | np.integer | np.floating
                )
                assert -100 <= team_stats["Fld"] <= 100  # Fielding runs

                assert isinstance(
                    team_stats["Payroll"], int | float | np.integer | np.floating
                )
                assert 50 <= team_stats["Payroll"] <= 400  # Payroll in millions

                assert isinstance(
                    team_stats["Payroll_Age"], int | float | np.integer | np.floating
                )
                assert 20 <= team_stats["Payroll_Age"] <= 40  # Team age

                assert isinstance(
                    team_stats["Luck"], int | float | np.integer | np.floating
                )
                assert -100 <= team_stats["Luck"] <= 100  # Luck value
