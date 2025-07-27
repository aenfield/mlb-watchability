"""Tests for the prompt CLI command."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from mlb_watchability.game_scores import GameScore
from mlb_watchability.prompt_cli import app as prompt_app
from mlb_watchability.prompt_cli import generate_prompt_filename


class TestPromptCli:
    """Test cases for the mlbw-prompt CLI command."""

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
                game_date="2025-07-27",
                away_team_nerd_score=8.2,
                home_team_nerd_score=7.9,
                average_team_nerd_score=8.05,
                away_pitcher_nerd_score=7.8,
                home_pitcher_nerd_score=6.2,
                average_pitcher_nerd_score=7.0,
                gnerd_score=15.05,
                away_team_nerd_stats=None,
                home_team_nerd_stats=None,
                away_pitcher_nerd_stats=None,
                home_pitcher_nerd_stats=None,
            ),
            GameScore(
                away_team="Boston Red Sox",
                home_team="Chicago Cubs",
                away_starter="Brayan Bello",
                home_starter="Shota Imanaga",
                game_time="19:15",
                game_date="2025-07-27",
                away_team_nerd_score=6.8,
                home_team_nerd_score=9.5,
                average_team_nerd_score=8.15,
                away_pitcher_nerd_score=3.9,
                home_pitcher_nerd_score=6.7,
                average_pitcher_nerd_score=5.3,
                gnerd_score=13.5,
                away_team_nerd_stats=None,
                home_team_nerd_stats=None,
                away_pitcher_nerd_stats=None,
                home_pitcher_nerd_stats=None,
            ),
        ]

    def test_generate_prompt_filename(self) -> None:
        """Test prompt filename generation."""
        result = generate_prompt_filename("2025-07-27", 0)
        assert result == "game_prompt_2025-07-27_game_0.md"

        result = generate_prompt_filename("2025-12-25", 3)
        assert result == "game_prompt_2025-12-25_game_3.md"

    @patch("mlb_watchability.prompt_cli.GameScore.from_games")
    @patch("mlb_watchability.prompt_cli.get_game_schedule")
    @patch("mlb_watchability.prompt_cli.extract_year_from_date")
    def test_prompt_cli_with_date_and_game_index(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test prompt CLI with specific date and game index."""
        # Setup mocks
        mock_extract_year.return_value = 2025
        mock_get_schedule.return_value = [
            {
                "away_team": "New York Yankees",
                "home_team": "Los Angeles Dodgers",
                "away_starter": "Gerrit Cole",
                "home_starter": "Walker Buehler",
                "time": "22:10",
            },
            {
                "away_team": "Boston Red Sox",
                "home_team": "Chicago Cubs",
                "away_starter": "Brayan Bello",
                "home_starter": "Shota Imanaga",
                "time": "19:15",
            },
        ]
        mock_calculate_scores.return_value = self.create_sample_game_scores()

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run CLI command with date and game index
                result = self.runner.invoke(prompt_app, ["2025-07-27", "1"])

                # Check that command succeeded
                assert result.exit_code == 0
                assert (
                    "Game prompt file generated: game_prompt_2025-07-27_game_1.md"
                    in result.stdout
                )

                # Check that output file was created
                output_file = Path("game_prompt_2025-07-27_game_1.md")
                assert output_file.exists()

                # Check file contains expected content
                content = output_file.read_text(encoding="utf-8")
                assert "Boston Red Sox" in content  # Should be game index 1
                assert "Chicago Cubs" in content
                assert "Brayan Bello" in content
                assert "Shota Imanaga" in content

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.prompt_cli.get_today")
    @patch("mlb_watchability.prompt_cli.GameScore.from_games")
    @patch("mlb_watchability.prompt_cli.get_game_schedule")
    @patch("mlb_watchability.prompt_cli.extract_year_from_date")
    def test_prompt_cli_without_date_uses_today(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
        mock_get_today: MagicMock,
    ) -> None:
        """Test prompt CLI without date argument uses today's date."""
        # Setup mocks
        mock_get_today.return_value = "2025-07-28"
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
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run CLI command without date
                result = self.runner.invoke(prompt_app, [])

                # Check that command succeeded and used today's date
                assert result.exit_code == 0
                assert (
                    "Game prompt file generated: game_prompt_2025-07-28_game_0.md"
                    in result.stdout
                )

                # Check that output file was created with today's date
                output_file = Path("game_prompt_2025-07-28_game_0.md")
                assert output_file.exists()

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.prompt_cli.GameScore.from_games")
    @patch("mlb_watchability.prompt_cli.get_game_schedule")
    @patch("mlb_watchability.prompt_cli.extract_year_from_date")
    def test_prompt_cli_with_no_games(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test prompt CLI when no games are found."""
        # Setup mocks to return no games
        mock_extract_year.return_value = 2025
        mock_get_schedule.return_value = []
        mock_calculate_scores.return_value = []

        # Run the CLI command
        result = self.runner.invoke(prompt_app, ["2025-07-27"])

        # Check that command handles no games gracefully
        assert result.exit_code == 0
        assert "No games found for 2025-07-27" in result.stdout

    @patch("mlb_watchability.prompt_cli.GameScore.from_games")
    @patch("mlb_watchability.prompt_cli.get_game_schedule")
    @patch("mlb_watchability.prompt_cli.extract_year_from_date")
    def test_prompt_cli_with_invalid_game_index(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test prompt CLI with game index out of range."""
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
        mock_calculate_scores.return_value = self.create_sample_game_scores()[
            :1
        ]  # Only one game

        # Run CLI command with invalid game index
        result = self.runner.invoke(prompt_app, ["2025-07-27", "5"])

        # Check that command handles invalid index gracefully
        assert result.exit_code == 0
        assert "Game index 5 is out of range" in result.stdout

    @patch("mlb_watchability.prompt_cli.GameScore.from_games")
    @patch("mlb_watchability.prompt_cli.get_game_schedule")
    @patch("mlb_watchability.prompt_cli.extract_year_from_date")
    def test_prompt_cli_with_send_to_llm_flag(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test prompt CLI with --send-to-llm flag."""
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

        # Create a mock GameScore with a mocked LLM method
        mock_game_score = MagicMock()
        mock_game_score.away_team = "New York Yankees"
        mock_game_score.home_team = "Los Angeles Dodgers"
        mock_game_score.gnerd_score = 15.05
        mock_game_score.generate_formatted_prompt.return_value = "Mock prompt content"
        mock_game_score.get_description_from_llm_using_prompt.return_value = (
            "Mock LLM description",
            [{"title": "Mock Source", "url": "https://example.com"}],
        )

        mock_calculate_scores.return_value = [mock_game_score]

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run CLI command with --send-to-llm flag
                result = self.runner.invoke(
                    prompt_app, ["2025-07-27", "0", "--send-to-llm"]
                )

                # Check that command succeeded
                assert result.exit_code == 0
                assert (
                    "Game prompt file generated: game_prompt_2025-07-27_game_0.md"
                    in result.stdout
                )

                # Check that LLM output sections are present
                assert "LLM-GENERATED DESCRIPTION:" in result.stdout
                assert "Mock LLM description" in result.stdout
                assert "WEB SOURCES:" in result.stdout
                assert "Mock Source" in result.stdout

                # Verify the LLM method was called
                mock_game_score.get_description_from_llm_using_prompt.assert_called_once_with(
                    "Mock prompt content"
                )

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.prompt_cli.GameScore.from_games")
    @patch("mlb_watchability.prompt_cli.get_game_schedule")
    @patch("mlb_watchability.prompt_cli.extract_year_from_date")
    def test_prompt_cli_with_send_to_llm_flag_no_sources(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test prompt CLI with --send-to-llm flag when no web sources are returned."""
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

        # Create a mock GameScore with a mocked LLM method that returns no sources
        mock_game_score = MagicMock()
        mock_game_score.away_team = "New York Yankees"
        mock_game_score.home_team = "Los Angeles Dodgers"
        mock_game_score.gnerd_score = 15.05
        mock_game_score.generate_formatted_prompt.return_value = "Mock prompt content"
        mock_game_score.get_description_from_llm_using_prompt.return_value = (
            "Mock LLM description",
            [],  # No web sources
        )

        mock_calculate_scores.return_value = [mock_game_score]

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run CLI command with --send-to-llm flag
                result = self.runner.invoke(
                    prompt_app, ["2025-07-27", "0", "--send-to-llm"]
                )

                # Check that command succeeded
                assert result.exit_code == 0
                assert "Mock LLM description" in result.stdout
                assert "No web sources found." in result.stdout

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.prompt_cli.get_game_schedule")
    @patch("mlb_watchability.prompt_cli.extract_year_from_date")
    def test_prompt_cli_with_api_error(
        self, mock_extract_year: MagicMock, mock_get_schedule: MagicMock
    ) -> None:
        """Test prompt CLI when API call fails."""
        # Setup mocks to raise an exception
        mock_extract_year.return_value = 2025
        mock_get_schedule.side_effect = Exception("API Error")

        # Run the CLI command
        result = self.runner.invoke(prompt_app, ["2025-07-27"])

        # Check that command handles errors gracefully
        assert result.exit_code == 1

    @patch("mlb_watchability.prompt_cli.GameScore.from_games")
    @patch("mlb_watchability.prompt_cli.get_game_schedule")
    @patch("mlb_watchability.prompt_cli.extract_year_from_date")
    def test_prompt_cli_file_write_error(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test prompt CLI when file writing fails."""
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

        with patch("pathlib.Path.write_text", side_effect=OSError("Permission denied")):
            # Run the CLI command
            result = self.runner.invoke(prompt_app, ["2025-07-27"])

            # Check that command handles file write errors gracefully
            assert result.exit_code == 1
