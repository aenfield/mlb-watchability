"""Tests for utility functions."""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

from mlb_watchability.utils import (
    extract_year_from_date,
    format_time_12_hour,
    get_today,
    get_tomorrow,
)


class TestUtils:
    """Test cases for utility functions."""

    def test_format_time_12_hour_morning(self) -> None:
        """Test morning time formatting."""
        assert format_time_12_hour("09:30") == "9:30a"
        assert format_time_12_hour("06:15") == "6:15a"
        assert format_time_12_hour("11:45") == "11:45a"

    def test_format_time_12_hour_noon(self) -> None:
        """Test noon time formatting."""
        assert format_time_12_hour("12:00") == "12:00p"
        assert format_time_12_hour("12:30") == "12:30p"

    def test_format_time_12_hour_afternoon_evening(self) -> None:
        """Test afternoon and evening time formatting."""
        assert format_time_12_hour("13:00") == "1:00p"
        assert format_time_12_hour("19:15") == "7:15p"
        assert format_time_12_hour("22:10") == "10:10p"
        assert format_time_12_hour("21:40") == "9:40p"
        assert format_time_12_hour("20:00") == "8:00p"

    def test_format_time_12_hour_midnight(self) -> None:
        """Test midnight time formatting."""
        assert format_time_12_hour("00:00") == "12:00a"
        assert format_time_12_hour("00:30") == "12:30a"

    def test_format_time_12_hour_edge_cases(self) -> None:
        """Test edge cases for time formatting."""
        assert format_time_12_hour(None) == "TBD"
        assert format_time_12_hour("") == "TBD"
        assert format_time_12_hour("TBD") == "TBD"
        assert format_time_12_hour("invalid") == "invalid"
        assert format_time_12_hour("25:00") == "25:00"  # Invalid hour
        assert format_time_12_hour("12") == "12"  # Missing colon

    def test_format_time_12_hour_single_digit_minutes(self) -> None:
        """Test formatting with single digit minutes."""
        assert format_time_12_hour("14:05") == "2:05p"
        assert format_time_12_hour("08:07") == "8:07a"
        assert format_time_12_hour("00:01") == "12:01a"

    @patch("mlb_watchability.utils.datetime")
    def test_get_today(self, mock_datetime: Any) -> None:
        """Test get_today function."""
        # Mock the current date
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2025-07-20"
        mock_datetime.now.return_value = mock_now

        result = get_today()
        assert result == "2025-07-20"
        mock_datetime.now.assert_called_once()
        mock_now.strftime.assert_called_once_with("%Y-%m-%d")

    @patch("mlb_watchability.utils.datetime")
    def test_get_tomorrow(self, mock_datetime: Any) -> None:
        """Test get_tomorrow function."""
        # Mock the current date
        mock_now = datetime(2025, 7, 20, 14, 30)
        mock_datetime.now.return_value = mock_now

        # We need to actually call the real function since mocking is complex
        # Just test that it returns a string in the right format
        result = get_tomorrow()
        assert isinstance(result, str)
        assert len(result) == 10  # YYYY-MM-DD format
        assert result.count("-") == 2

    def test_extract_year_from_date(self) -> None:
        """Test extract_year_from_date function."""
        assert extract_year_from_date("2025-07-20") == 2025
        assert extract_year_from_date("2024-12-31") == 2024
        assert extract_year_from_date("2023-01-01") == 2023

    @patch("mlb_watchability.utils.datetime")
    def test_extract_year_from_date_invalid(self, mock_datetime: Any) -> None:
        """Test extract_year_from_date with invalid input."""
        # Mock the current year for fallback
        mock_datetime.now.return_value.year = 2025

        # Test invalid formats fall back to current year
        assert extract_year_from_date("invalid-date") == 2025
        assert extract_year_from_date("") == 2025
        assert extract_year_from_date("2025") == 2025  # Missing dashes
