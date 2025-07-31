"""Utility functions for MLB Watchability."""

from datetime import datetime, timedelta


def get_today() -> str:
    """Get today's date."""
    today = datetime.now()
    return today.strftime("%Y-%m-%d")


def get_tomorrow() -> str:
    """Get tomorrow's date."""
    tomorrow = datetime.now() + timedelta(days=1)
    return tomorrow.strftime("%Y-%m-%d")


def extract_year_from_date(date_str: str) -> int:
    """Extract year from a date string in YYYY-MM-DD format."""
    try:
        return int(date_str.split("-")[0])
    except (ValueError, IndexError):
        # Default to current year if parsing fails
        return datetime.now().year


def format_time_12_hour(time_str: str | None) -> str:
    """Convert 24-hour time format to 12-hour format with 'a' or 'p' suffix."""
    if not time_str or time_str == "TBD":
        return "TBD"

    try:
        dt = datetime.strptime(time_str, "%H:%M")
    except ValueError:
        # Return original if parsing fails
        return time_str
    else:
        hour_12 = dt.hour % 12 or 12  # Handle midnight correctly
        minute = dt.minute
        suffix = "a" if dt.hour < 12 else "p"  # noqa: PLR2004
        return f"{hour_12}:{minute:02d}{suffix}"


def format_time_24_hour(time_str: str | None) -> str:
    """Convert time string to 24-hour format for sorting purposes."""
    if not time_str or time_str == "TBD":
        return "TBD"

    try:
        dt = datetime.strptime(time_str, "%H:%M")
    except ValueError:
        # Return original if parsing fails
        return time_str
    else:
        return f"{dt.hour:02d}{dt.minute:02d}"
