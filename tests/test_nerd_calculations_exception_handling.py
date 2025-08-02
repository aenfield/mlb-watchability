"""Tests for exception handling in NERD calculation functions."""

from unittest.mock import patch

import pytest

from mlb_watchability.pitcher_stats import calculate_detailed_pitcher_nerd_scores
from mlb_watchability.team_stats import calculate_detailed_team_nerd_scores


class TestNerdCalculationsExceptionHandling:
    """Test exception propagation in NERD calculation functions."""

    def test_calculate_detailed_pitcher_nerd_scores_propagates_exceptions(self) -> None:
        """Test that pitcher NERD calculation propagates pybaseball exceptions."""

        with patch(
            "mlb_watchability.pitcher_stats.get_all_pitcher_stats_objects"
        ) as mock_get:
            # Mock the underlying get_all_pitcher_stats to raise RuntimeError
            mock_get.side_effect = RuntimeError(
                "Failed to retrieve pitcher statistics for season 2025: Error accessing 'https://www.fangraphs.com/leaders-legacy.aspx'. Received status code 403"
            )

            # Expect the exception to bubble up, not return empty dict
            with pytest.raises(
                RuntimeError, match="Failed to retrieve pitcher statistics"
            ):
                calculate_detailed_pitcher_nerd_scores(2025)

    def test_calculate_detailed_team_nerd_scores_propagates_exceptions(self) -> None:
        """Test that team NERD calculation propagates pybaseball exceptions."""

        with patch(
            "mlb_watchability.team_stats.get_all_team_stats_objects"
        ) as mock_get:
            mock_get.side_effect = RuntimeError(
                "Failed to retrieve team statistics for season 2025: Error accessing 'https://www.fangraphs.com/leaders-legacy.aspx'. Received status code 403"
            )

            with pytest.raises(
                RuntimeError, match="Failed to retrieve team statistics"
            ):
                calculate_detailed_team_nerd_scores(2025)

    def test_calculate_detailed_pitcher_nerd_scores_propagates_other_exceptions(
        self,
    ) -> None:
        """Test that pitcher NERD calculation propagates other types of exceptions."""

        with patch(
            "mlb_watchability.pitcher_stats.get_all_pitcher_stats_objects"
        ) as mock_get:
            # Test with a different type of exception
            mock_get.side_effect = ValueError("Invalid season parameter")

            with pytest.raises(ValueError, match="Invalid season parameter"):
                calculate_detailed_pitcher_nerd_scores(2025)

    def test_calculate_detailed_team_nerd_scores_propagates_other_exceptions(
        self,
    ) -> None:
        """Test that team NERD calculation propagates other types of exceptions."""

        with patch(
            "mlb_watchability.team_stats.get_all_team_stats_objects"
        ) as mock_get:
            # Test with a different type of exception
            mock_get.side_effect = ConnectionError("Network connection failed")

            with pytest.raises(ConnectionError, match="Network connection failed"):
                calculate_detailed_team_nerd_scores(2025)
