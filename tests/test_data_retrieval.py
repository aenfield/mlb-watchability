"""Tests for the data retrieval module."""

from unittest.mock import patch

import pytest

from mlb_watchability.data_retrieval import get_game_schedule


#@pytest.mark.skip(reason="Disabled until I do a new non-pybaseball impl")
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

        with patch("mlb_watchability.data_retrieval.statsapi.schedule") as mock_schedule:
            mock_schedule.return_value = mock_schedule_data
            result = get_game_schedule(test_date)

            assert result == expected_games
            mock_schedule.assert_called_once()

    def test_get_game_schedule_with_empty_schedule(self) -> None:
        """Test that get_game_schedule returns empty list when no games scheduled."""

        test_date = "2024-12-01"  # Off-season date
        mock_empty_schedule = []

        with patch("mlb_watchability.data_retrieval.statsapi.schedule") as mock_schedule:
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

        with patch("mlb_watchability.data_retrieval.statsapi.schedule") as mock_schedule:
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
        mock_empty_schedule = []

        with patch("mlb_watchability.data_retrieval.statsapi.schedule") as mock_schedule:
            mock_schedule.return_value = mock_empty_schedule
            result = get_game_schedule(future_date)

            assert result == []

    def test_get_game_schedule_with_api_error(self) -> None:
        """Test that get_game_schedule handles API errors gracefully."""

        test_date = "2024-07-15"

        with patch("mlb_watchability.data_retrieval.statsapi.schedule") as mock_schedule:
            mock_schedule.side_effect = Exception("API Error")

            with pytest.raises(RuntimeError, match="Failed to retrieve game schedule"):
                get_game_schedule(test_date)

    def test_get_game_schedule_date_parsing(self) -> None:
        """Test that get_game_schedule properly validates date format."""

        invalid_dates = [
            "2024-13-01",  # Invalid month
            "2024-02-30",  # Invalid day
            "24-07-15",    # Wrong year format
            "2024/07/15",  # Wrong separator
            "",            # Empty string
        ]

        for invalid_date in invalid_dates:
            with pytest.raises(ValueError, match="Invalid date format"):
                get_game_schedule(invalid_date)


#@pytest.mark.skip(reason="Disabled until I do a new non-pybaseball impl")
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
                assert game["time"] is not None  # Time should be available in MLB-StatsAPI (Eastern time)
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
            required_keys = ["date", "away_team", "home_team", "time", "away_starter", "home_starter"]
            for key in required_keys:
                assert key in game

            # Date should match what we requested
            assert game["date"] == test_date
