"""Tests for time formatting functionality."""

from mlb_watchability.cli import format_time_12_hour


class TestTimeFormatting:
    """Test cases for 12-hour time formatting."""

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
