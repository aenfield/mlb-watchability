"""Tests for the llm-model parameter in the markdown CLI command."""

import os
import tempfile
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from mlb_watchability.game_scores import CANNED_GAME_DESCRIPTION, GameScore
from mlb_watchability.markdown_cli import app as markdown_app


class TestMarkdownCliLlmModel:
    """Tests for the llm-model parameter in markdown CLI."""

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
                game_time="19:10",
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
                game_description=CANNED_GAME_DESCRIPTION,
                game_description_sources=[],
            ),
        ]

    @patch("mlb_watchability.markdown_cli.GameScore.from_games")
    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    def test_markdown_cli_with_llm_model_normal(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test markdown CLI with --llm-model normal parameter."""
        # Setup mocks
        mock_extract_year.return_value = 2025
        mock_get_schedule.return_value = [
            {
                "away_team": "Seattle Mariners",
                "home_team": "Los Angeles Dodgers",
                "away_starter": "Logan Gilbert",
                "home_starter": "Walker Buehler",
                "time": "19:10",
            }
        ]
        mock_calculate_scores.return_value = self.create_sample_game_scores()

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run the CLI command with --llm-model normal
                result = self.runner.invoke(
                    markdown_app,
                    [
                        "2025-07-20",
                        "--game-desc-source",
                        "llm",
                        "--llm-model",
                        "normal",
                    ],
                )

                # Check that command succeeded
                assert result.exit_code == 0
                assert (
                    "Markdown file generated: mlb_what_to_watch_2025_07_20.md"
                    in result.stdout
                )

                # Verify that GameScore.from_games was called with generic model type "normal"
                mock_calculate_scores.assert_called_once()
                call_args = mock_calculate_scores.call_args
                assert call_args[1]["model"] == "normal"
                assert call_args[1]["provider"] == "anthropic"  # default provider

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.markdown_cli.GameScore.from_games")
    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    def test_markdown_cli_with_llm_model_cheap(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test markdown CLI with --llm-model cheap parameter."""
        # Setup mocks
        mock_extract_year.return_value = 2025
        mock_get_schedule.return_value = [
            {
                "away_team": "Boston Red Sox",
                "home_team": "Chicago Cubs",
                "away_starter": "Brayan Bello",
                "home_starter": "Shota Imanaga",
                "time": "16:15",
            }
        ]
        mock_calculate_scores.return_value = self.create_sample_game_scores()

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run the CLI command with --llm-model cheap
                result = self.runner.invoke(
                    markdown_app,
                    ["2025-07-20", "--game-desc-source", "llm", "--llm-model", "cheap"],
                )

                # Check that command succeeded
                assert result.exit_code == 0
                assert (
                    "Markdown file generated: mlb_what_to_watch_2025_07_20.md"
                    in result.stdout
                )

                # Verify that GameScore.from_games was called with generic model type "cheap"
                mock_calculate_scores.assert_called_once()
                call_args = mock_calculate_scores.call_args
                assert call_args[1]["model"] == "cheap"
                assert call_args[1]["provider"] == "anthropic"  # default provider

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.markdown_cli.GameScore.from_games")
    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    def test_markdown_cli_with_llm_model_default(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test markdown CLI with default llm-model parameter (should be normal)."""
        # Setup mocks
        mock_extract_year.return_value = 2025
        mock_get_schedule.return_value = [
            {
                "away_team": "New York Yankees",
                "home_team": "Los Angeles Dodgers",
                "away_starter": "Gerrit Cole",
                "home_starter": "Walker Buehler",
                "time": "19:10",
            }
        ]
        mock_calculate_scores.return_value = self.create_sample_game_scores()

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run the CLI command without --llm-model (should default to normal)
                result = self.runner.invoke(
                    markdown_app, ["2025-07-20", "--game-desc-source", "llm"]
                )

                # Check that command succeeded
                assert result.exit_code == 0
                assert (
                    "Markdown file generated: mlb_what_to_watch_2025_07_20.md"
                    in result.stdout
                )

                # Verify that GameScore.from_games was called with generic model type "normal" (default)
                mock_calculate_scores.assert_called_once()
                call_args = mock_calculate_scores.call_args
                assert call_args[1]["model"] == "normal"
                assert call_args[1]["provider"] == "anthropic"  # default provider

            finally:
                os.chdir(original_cwd)

    def test_markdown_cli_with_invalid_llm_model(self) -> None:
        """Test markdown CLI with invalid --llm-model parameter."""
        # Run the CLI command with invalid llm-model
        result = self.runner.invoke(
            markdown_app,
            ["2025-07-20", "--game-desc-source", "llm", "--llm-model", "invalid"],
        )

        # Check that command fails with error
        assert result.exit_code == 1
        # Error message might be in output or stderr - check both
        error_message = "Error: llm_model must be 'normal' or 'cheap', not 'invalid'"
        assert error_message in result.output or error_message in getattr(
            result, "stderr", ""
        )

    @patch("mlb_watchability.markdown_cli.GameScore.from_games")
    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    def test_markdown_cli_llm_model_with_canned_descriptions(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test that llm-model parameter is passed even when using canned descriptions."""
        # Setup mocks
        mock_extract_year.return_value = 2025
        mock_get_schedule.return_value = [
            {
                "away_team": "Tampa Bay Rays",
                "home_team": "Seattle Mariners",
                "away_starter": "Ryan Pepiot",
                "home_starter": "George Kirby",
                "time": "22:40",
            }
        ]
        mock_calculate_scores.return_value = self.create_sample_game_scores()

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run the CLI command with canned descriptions and cheap model
                result = self.runner.invoke(
                    markdown_app,
                    [
                        "2025-07-20",
                        "--game-desc-source",
                        "canned",
                        "--llm-model",
                        "cheap",
                    ],
                )

                # Check that command succeeded
                assert result.exit_code == 0

                # Verify that GameScore.from_games was called with ANTHROPIC_MODEL_CHEAP
                # even though descriptions are canned (model parameter should still be passed)
                mock_calculate_scores.assert_called_once()
                call_args = mock_calculate_scores.call_args
                assert call_args[1]["model"] == "cheap"
                assert call_args[1]["provider"] == "anthropic"  # default provider

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.markdown_cli.GameScore.from_games")
    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    def test_markdown_cli_with_llm_model_provider_anthropic(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test markdown CLI with --llm-model-provider anthropic parameter."""
        # Setup mocks
        mock_extract_year.return_value = 2025
        mock_get_schedule.return_value = [
            {
                "away_team": "Seattle Mariners",
                "home_team": "Los Angeles Dodgers",
                "away_starter": "Logan Gilbert",
                "home_starter": "Walker Buehler",
                "time": "19:10",
            }
        ]
        mock_calculate_scores.return_value = self.create_sample_game_scores()

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run the CLI command with --llm-model-provider anthropic
                result = self.runner.invoke(
                    markdown_app,
                    [
                        "2025-07-20",
                        "--game-desc-source",
                        "llm",
                        "--llm-model-provider",
                        "anthropic",
                        "--llm-model",
                        "cheap",
                    ],
                )

                # Check that command succeeded
                assert result.exit_code == 0
                assert (
                    "Markdown file generated: mlb_what_to_watch_2025_07_20.md"
                    in result.stdout
                )

                # Verify that GameScore.from_games was called with anthropic provider
                mock_calculate_scores.assert_called_once()
                call_args = mock_calculate_scores.call_args
                assert call_args[1]["provider"] == "anthropic"
                assert call_args[1]["model"] == "cheap"

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.markdown_cli.GameScore.from_games")
    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    def test_markdown_cli_with_llm_model_provider_openai(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test markdown CLI with --llm-model-provider openai parameter."""
        # Setup mocks
        mock_extract_year.return_value = 2025
        mock_get_schedule.return_value = [
            {
                "away_team": "Seattle Mariners",
                "home_team": "Los Angeles Dodgers",
                "away_starter": "Logan Gilbert",
                "home_starter": "Walker Buehler",
                "time": "19:10",
            }
        ]
        mock_calculate_scores.return_value = self.create_sample_game_scores()

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run the CLI command with --llm-model-provider openai
                result = self.runner.invoke(
                    markdown_app,
                    [
                        "2025-07-20",
                        "--game-desc-source",
                        "llm",
                        "--llm-model-provider",
                        "openai",
                        "--llm-model",
                        "normal",
                    ],
                )

                # Check that command succeeded
                assert result.exit_code == 0
                assert (
                    "Markdown file generated: mlb_what_to_watch_2025_07_20.md"
                    in result.stdout
                )

                # Verify that GameScore.from_games was called with openai provider
                mock_calculate_scores.assert_called_once()
                call_args = mock_calculate_scores.call_args
                assert call_args[1]["provider"] == "openai"
                assert call_args[1]["model"] == "normal"

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.markdown_cli.GameScore.from_games")
    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    def test_markdown_cli_with_llm_model_provider_default(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test markdown CLI with default provider (should be anthropic)."""
        # Setup mocks
        mock_extract_year.return_value = 2025
        mock_get_schedule.return_value = [
            {
                "away_team": "Seattle Mariners",
                "home_team": "Los Angeles Dodgers",
                "away_starter": "Logan Gilbert",
                "home_starter": "Walker Buehler",
                "time": "19:10",
            }
        ]
        mock_calculate_scores.return_value = self.create_sample_game_scores()

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run the CLI command without --llm-model-provider (should default to anthropic)
                result = self.runner.invoke(
                    markdown_app,
                    [
                        "2025-07-20",
                        "--game-desc-source",
                        "llm",
                        "--llm-model",
                        "normal",
                    ],
                )

                # Check that command succeeded
                assert result.exit_code == 0
                assert (
                    "Markdown file generated: mlb_what_to_watch_2025_07_20.md"
                    in result.stdout
                )

                # Verify that GameScore.from_games was called with default anthropic provider
                mock_calculate_scores.assert_called_once()
                call_args = mock_calculate_scores.call_args
                assert call_args[1]["provider"] == "anthropic"  # default
                assert call_args[1]["model"] == "normal"

            finally:
                os.chdir(original_cwd)

    def test_markdown_cli_with_invalid_llm_model_provider(self) -> None:
        """Test markdown CLI with invalid --llm-model-provider parameter."""
        # Run the CLI command with invalid provider
        result = self.runner.invoke(
            markdown_app,
            [
                "2025-07-20",
                "--game-desc-source",
                "llm",
                "--llm-model-provider",
                "invalid",
            ],
        )

        # Check that command fails with error
        assert result.exit_code == 1
        # Error message might be in output or stderr - check both
        error_message = (
            "Error: llm_model_provider must be 'anthropic' or 'openai', not 'invalid'"
        )
        assert error_message in result.output or error_message in getattr(
            result, "stderr", ""
        )
