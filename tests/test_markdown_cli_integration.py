"""Integration tests for the markdown CLI command."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from mlb_watchability.game_scores import GameScore
from mlb_watchability.markdown_cli import app as markdown_app


class TestMarkdownCliIntegration:
    """Integration tests for the mlbw-markdown CLI command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def create_sample_game_scores(self) -> list[GameScore]:
        """Create sample game scores for testing."""
        return [
            GameScore(
                away_team="New York Yankees",
                home_team="Los Angeles Dodgers",
                away_starter="Gerrit Cole",
                home_starter="Walker Buehler",
                game_time="22:10",
                away_team_nerd=8.2,
                home_team_nerd=7.9,
                average_team_nerd=8.05,
                away_pitcher_nerd=7.8,
                home_pitcher_nerd=6.2,
                average_pitcher_nerd=7.0,
                gnerd_score=15.05,
            ),
            GameScore(
                away_team="Boston Red Sox",
                home_team="Chicago Cubs",
                away_starter="Brayan Bello",
                home_starter="Shota Imanaga",
                game_time="19:15",
                away_team_nerd=6.8,
                home_team_nerd=9.5,
                average_team_nerd=8.15,
                away_pitcher_nerd=3.9,
                home_pitcher_nerd=6.7,
                average_pitcher_nerd=5.3,
                gnerd_score=13.5,
            ),
        ]

    @patch("mlb_watchability.markdown_cli.calculate_game_scores")
    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    def test_markdown_cli_with_date_argument(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test markdown CLI with a specific date argument."""
        # Setup mocks
        mock_extract_year.return_value = 2025
        mock_get_schedule.return_value = [
            {
                "away_team": "New York Yankees",
                "home_team": "Los Angeles Dodgers",
                "away_starter": "Gerrit Cole",
                "home_starter": "Walker Buehler",
                "time": "22:10",
            }
        ]
        mock_calculate_scores.return_value = self.create_sample_game_scores()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory so output file is created there
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run the CLI command
                result = self.runner.invoke(markdown_app, ["2025-07-20"])

                # Check that command succeeded
                assert result.exit_code == 0
                assert (
                    "Markdown file generated: mlb_what_to_watch_2025_07_20.md"
                    in result.stdout
                )

                # Check that output file was created
                output_file = Path("mlb_what_to_watch_2025_07_20.md")
                assert output_file.exists()

                # Check file contents
                content = output_file.read_text(encoding="utf-8")

                # Check metadata block
                assert "---" in content
                assert 'title: "MLB: What to watch on July 20, 2025"' in content
                assert "date: 2025-07-20" in content
                assert "tags: mlbw" in content

                # Check intro and footer text
                assert "Watch these games today:" in content
                assert "And here's a footer, which someone can modify later." in content

                # Check table header with EDT timezone
                assert "| Score | Time (EDT) |" in content

                # Check game data
                assert "New York Yankees" in content
                assert "Los Angeles Dodgers" in content
                assert "15.1" in content  # gNERD score

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.markdown_cli.get_today")
    @patch("mlb_watchability.markdown_cli.calculate_game_scores")
    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    def test_markdown_cli_without_date_argument(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
        mock_get_today: MagicMock,
    ) -> None:
        """Test markdown CLI without date argument (should use today)."""
        # Setup mocks
        mock_get_today.return_value = "2025-07-21"
        mock_extract_year.return_value = 2025
        mock_get_schedule.return_value = [
            {
                "away_team": "Boston Red Sox",
                "home_team": "Chicago Cubs",
                "away_starter": "Brayan Bello",
                "home_starter": "Shota Imanaga",
                "time": "19:15",
            }
        ]
        mock_calculate_scores.return_value = self.create_sample_game_scores()

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run the CLI command without date argument
                result = self.runner.invoke(markdown_app, [])

                # Check that command succeeded and used today's date
                assert result.exit_code == 0
                assert (
                    "Markdown file generated: mlb_what_to_watch_2025_07_21.md"
                    in result.stdout
                )

                # Check that output file was created with today's date
                output_file = Path("mlb_what_to_watch_2025_07_21.md")
                assert output_file.exists()

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.markdown_cli.calculate_game_scores")
    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    def test_markdown_cli_with_no_games(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test markdown CLI when no games are found."""
        # Setup mocks to return no games
        mock_extract_year.return_value = 2025
        mock_get_schedule.return_value = []
        mock_calculate_scores.return_value = []

        # Run the CLI command
        result = self.runner.invoke(markdown_app, ["2025-07-20"])

        # Check that command handles no games gracefully
        assert result.exit_code == 0
        assert "No games found for 2025-07-20" in result.stdout

    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    def test_markdown_cli_with_api_error(
        self, mock_extract_year: MagicMock, mock_get_schedule: MagicMock
    ) -> None:
        """Test markdown CLI when API call fails."""
        # Setup mocks to raise an exception
        mock_extract_year.return_value = 2025
        mock_get_schedule.side_effect = Exception("API Error")

        # Run the CLI command
        result = self.runner.invoke(markdown_app, ["2025-07-20"])

        # Check that command handles errors gracefully
        assert result.exit_code == 1
        # Error messages may go to stderr, so we just check exit code

    def test_markdown_cli_logging_output(self) -> None:
        """Test that the CLI produces appropriate logging output."""
        with (
            patch(
                "mlb_watchability.markdown_cli.get_game_schedule"
            ) as mock_get_schedule,
            patch(
                "mlb_watchability.markdown_cli.calculate_game_scores"
            ) as mock_calculate_scores,
            patch(
                "mlb_watchability.markdown_cli.extract_year_from_date"
            ) as mock_extract_year,
        ):

            # Setup mocks
            mock_extract_year.return_value = 2025
            mock_get_schedule.return_value = [
                {"away_team": "Test", "home_team": "Test2"}
            ]
            mock_calculate_scores.return_value = self.create_sample_game_scores()

            with tempfile.TemporaryDirectory() as temp_dir:
                original_cwd = os.getcwd()
                try:
                    os.chdir(temp_dir)

                    # Run the CLI command
                    result = self.runner.invoke(markdown_app, ["2025-07-20"])

                    # Check for successful completion
                    assert (
                        "Markdown file generated: mlb_what_to_watch_2025_07_20.md"
                        in result.stdout
                    )

                finally:
                    os.chdir(original_cwd)
