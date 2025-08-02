"""Integration tests for the markdown CLI command."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import requests
from typer.testing import CliRunner

from mlb_watchability.game_scores import CANNED_GAME_DESCRIPTION, GameScore
from mlb_watchability.markdown_cli import app as markdown_app
from mlb_watchability.pitcher_stats import PitcherNerdStats, PitcherStats
from mlb_watchability.team_stats import TeamNerdStats, TeamStats


class TestMarkdownCliIntegration:
    """Integration tests for the mlbw-markdown CLI command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def create_sample_game_scores(self) -> list[GameScore]:
        """Create sample game scores for testing."""
        # Create sample detailed stats for testing
        {
            "NYY": TeamNerdStats(
                team_stats=TeamStats(
                    name="NYY",
                    batting_runs=10.0,
                    barrel_rate=0.08,
                    baserunning_runs=5.0,
                    fielding_runs=15.0,
                    payroll=200.0,
                    age=28.5,
                    luck=10.0,
                ),
                z_batting_runs=1.0,
                z_barrel_rate=0.5,
                z_baserunning_runs=0.3,
                z_fielding_runs=1.2,
                z_payroll=-0.8,
                z_age=-0.5,
                z_luck=0.4,
                adjusted_payroll=0.8,
                adjusted_age=0.5,
                adjusted_luck=0.4,
                tnerd_score=8.2,
            ),
            "LAD": TeamNerdStats(
                team_stats=TeamStats(
                    name="LAD",
                    batting_runs=15.0,
                    barrel_rate=0.09,
                    baserunning_runs=7.0,
                    fielding_runs=12.0,
                    payroll=250.0,
                    age=29.0,
                    luck=8.0,
                ),
                z_batting_runs=1.2,
                z_barrel_rate=0.7,
                z_baserunning_runs=0.5,
                z_fielding_runs=1.0,
                z_payroll=-1.0,
                z_age=-0.3,
                z_luck=0.3,
                adjusted_payroll=1.0,
                adjusted_age=0.3,
                adjusted_luck=0.3,
                tnerd_score=7.9,
            ),
            "BOS": TeamNerdStats(
                team_stats=TeamStats(
                    name="BOS",
                    batting_runs=8.0,
                    barrel_rate=0.075,
                    baserunning_runs=4.0,
                    fielding_runs=8.0,
                    payroll=180.0,
                    age=27.5,
                    luck=5.0,
                ),
                z_batting_runs=0.8,
                z_barrel_rate=0.3,
                z_baserunning_runs=0.2,
                z_fielding_runs=0.8,
                z_payroll=-0.3,
                z_age=-0.8,
                z_luck=0.2,
                adjusted_payroll=0.3,
                adjusted_age=0.8,
                adjusted_luck=0.2,
                tnerd_score=6.8,
            ),
            "CHC": TeamNerdStats(
                team_stats=TeamStats(
                    name="CHC",
                    batting_runs=18.0,
                    barrel_rate=0.095,
                    baserunning_runs=9.0,
                    fielding_runs=16.0,
                    payroll=220.0,
                    age=28.0,
                    luck=12.0,
                ),
                z_batting_runs=1.4,
                z_barrel_rate=0.8,
                z_baserunning_runs=0.7,
                z_fielding_runs=1.3,
                z_payroll=-0.9,
                z_age=-0.5,
                z_luck=0.5,
                adjusted_payroll=0.9,
                adjusted_age=0.5,
                adjusted_luck=0.5,
                tnerd_score=9.5,
            ),
        }

        {
            "Gerrit Cole": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Gerrit Cole",
                    team="NYY",
                    xfip_minus=85.0,
                    swinging_strike_rate=0.15,
                    strike_rate=0.68,
                    velocity=96.0,
                    age=32,
                    pace=20.0,
                    luck=3.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-1.5,
                z_swinging_strike_rate=1.8,
                z_strike_rate=1.0,
                z_velocity=1.5,
                z_age=0.5,
                z_pace=-1.0,
                adjusted_velocity=1.5,
                adjusted_age=0.0,
                adjusted_luck=0.15,
                pnerd_score=7.8,
            ),
            "Walker Buehler": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Walker Buehler",
                    team="LAD",
                    xfip_minus=92.0,
                    swinging_strike_rate=0.13,
                    strike_rate=0.65,
                    velocity=94.0,
                    age=29,
                    pace=22.0,
                    luck=8.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-0.8,
                z_swinging_strike_rate=1.2,
                z_strike_rate=0.7,
                z_velocity=0.8,
                z_age=0.0,
                z_pace=0.0,
                adjusted_velocity=0.8,
                adjusted_age=0.0,
                adjusted_luck=0.4,
                pnerd_score=6.2,
            ),
            "Brayan Bello": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Brayan Bello",
                    team="BOS",
                    xfip_minus=105.0,
                    swinging_strike_rate=0.10,
                    strike_rate=0.62,
                    velocity=92.0,
                    age=25,
                    pace=24.0,
                    luck=2.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=0.5,
                z_swinging_strike_rate=0.5,
                z_strike_rate=0.0,
                z_velocity=0.2,
                z_age=-0.8,
                z_pace=0.5,
                adjusted_velocity=0.2,
                adjusted_age=0.8,
                adjusted_luck=0.1,
                pnerd_score=3.9,
            ),
            "Shota Imanaga": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Shota Imanaga",
                    team="CHC",
                    xfip_minus=88.0,
                    swinging_strike_rate=0.14,
                    strike_rate=0.67,
                    velocity=91.0,
                    age=31,
                    pace=21.0,
                    luck=6.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-1.2,
                z_swinging_strike_rate=1.5,
                z_strike_rate=0.9,
                z_velocity=0.0,
                z_age=0.2,
                z_pace=-0.3,
                adjusted_velocity=0.0,
                adjusted_age=0.0,
                adjusted_luck=0.3,
                pnerd_score=6.7,
            ),
        }

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
            GameScore(
                away_team="Boston Red Sox",
                home_team="Chicago Cubs",
                away_starter="Brayan Bello",
                home_starter="Shota Imanaga",
                game_time="16:15",
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
                game_description=None,
                game_description_sources=None,
            ),
        ]

    @patch("mlb_watchability.markdown_cli.GameScore.from_games")
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
                "time": "19:10",
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
                # no longer needed, at least for now

                # Check table header with PT timezone
                assert "| Score | Time (PT) |" in content

                # Check game data
                assert "New York Yankees" in content
                assert "Los Angeles Dodgers" in content
                assert "15.1" in content  # gNERD score

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.markdown_cli.get_today")
    @patch("mlb_watchability.markdown_cli.GameScore.from_games")
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
                "time": "16:15",
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

    @patch("mlb_watchability.markdown_cli.GameScore.from_games")
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
                "mlb_watchability.markdown_cli.GameScore.from_games"
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

    @patch("mlb_watchability.markdown_cli.GameScore.from_games")
    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    def test_markdown_cli_with_game_descriptions_flag(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test markdown CLI with --game-descriptions flag enabled."""
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

        # Create a game with canned description to test new functionality
        mariners_game = GameScore(
            away_team="Seattle Mariners",
            home_team="Los Angeles Dodgers",
            away_starter="Logan Gilbert",
            home_starter="Walker Buehler",
            game_time="19:10",
            game_date="2025-07-27",
            away_team_nerd_score=7.5,
            home_team_nerd_score=8.9,
            average_team_nerd_score=8.2,
            away_pitcher_nerd_score=6.8,
            home_pitcher_nerd_score=7.2,
            average_pitcher_nerd_score=7.0,
            gnerd_score=15.2,
            away_team_nerd_stats=None,
            home_team_nerd_stats=None,
            away_pitcher_nerd_stats=None,
            home_pitcher_nerd_stats=None,
            game_description=CANNED_GAME_DESCRIPTION,
            game_description_sources=[],
        )
        mock_calculate_scores.return_value = [mariners_game]

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run the CLI command with --game-desc-source canned
                result = self.runner.invoke(
                    markdown_app, ["2025-07-20", "--game-desc-source", "canned"]
                )

                # Check that command succeeded
                assert result.exit_code == 0
                assert (
                    "Markdown file generated: mlb_what_to_watch_2025_07_20.md"
                    in result.stdout
                )

                # Check that output file was created
                output_file = Path("mlb_what_to_watch_2025_07_20.md")
                assert output_file.exists()

                # Check file contents include description sections
                content = output_file.read_text(encoding="utf-8")

                # Should contain Description sections
                assert "### Summary" in content

                # Should contain canned description text
                assert "A concise summary of this compelling matchup" in content
                assert "distinct strengths and strategic approaches" in content

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.markdown_cli.GameScore.from_games")
    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    def test_markdown_cli_without_game_descriptions_flag(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test markdown CLI without --game-descriptions flag (default behavior)."""
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

                # Run the CLI command without --game-descriptions flag
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

                # Check file contents do NOT include description sections
                content = output_file.read_text(encoding="utf-8")

                # Should NOT contain Description sections
                assert "### Summary" not in content

                # Should still contain the detail sections but without descriptions
                assert "# Detail" in content
                assert "New York Yankees" in content
                assert "Los Angeles Dodgers" in content

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.markdown_cli.GameScore.from_games")
    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    def test_markdown_cli_with_generic_game_descriptions(
        self,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test markdown CLI with --game-descriptions flag for non-Mariners games."""
        # Setup mocks
        mock_extract_year.return_value = 2025
        mock_get_schedule.return_value = [
            {
                "away_team": "New York Yankees",
                "home_team": "Boston Red Sox",
                "away_starter": "Gerrit Cole",
                "home_starter": "Brayan Bello",
                "time": "16:15",
            }
        ]
        mock_calculate_scores.return_value = self.create_sample_game_scores()

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run the CLI command with --game-desc-source canned
                result = self.runner.invoke(
                    markdown_app, ["2025-07-20", "--game-desc-source", "canned"]
                )

                # Check that command succeeded
                assert result.exit_code == 0

                # Check that output file was created
                output_file = Path("mlb_what_to_watch_2025_07_20.md")
                assert output_file.exists()

                # Check file contents include generic description sections
                content = output_file.read_text(encoding="utf-8")

                # Should contain Description sections
                assert "### Summary" in content

                # Should contain generic description text (not Mariners-specific)
                assert "A concise summary of this compelling matchup" in content
                assert "distinct strengths and strategic approaches" in content

                # Should NOT contain Mariners-specific text
                assert "Seattle Mariners continue their pursuit" not in content

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.markdown_cli.GameScore.from_games")
    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    @patch("mlb_watchability.markdown_cli.extract_year_from_date")
    @patch("mlb_watchability.markdown_cli.load_dotenv")
    def test_env_loading_is_called(
        self,
        mock_load_dotenv: MagicMock,
        mock_extract_year: MagicMock,
        mock_get_schedule: MagicMock,
        mock_calculate_scores: MagicMock,
    ) -> None:
        """Test that load_dotenv is called when the CLI runs."""
        # Mock return value to simulate .env file found
        mock_load_dotenv.return_value = True

        # Setup other mocks for minimal functionality
        mock_extract_year.return_value = 2025
        mock_get_schedule.return_value = []  # No games to avoid complex mocking
        mock_calculate_scores.return_value = []

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Run the CLI command (this will trigger main function)
                result = self.runner.invoke(markdown_app, ["2025-07-28"])

                # Check that the command succeeds (even with no games)
                assert result.exit_code == 0

                # Verify that load_dotenv was called
                mock_load_dotenv.assert_called_once()

            finally:
                os.chdir(original_cwd)

    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    def test_markdown_cli_fails_when_pitcher_stats_raises_exception(
        self, mock_schedule: MagicMock
    ) -> None:
        """Test that markdown CLI fails fast when pitcher stats API returns 403 error."""
        # Mock get_game_schedule to return valid games
        mock_schedule.return_value = [
            {
                "date": "2025-07-31",
                "away_team": "Tampa Bay Rays",
                "home_team": "New York Yankees",
                "time": "19:05",
                "away_starter": "Ryan Pepiot",
                "home_starter": "Marcus Stroman",
            }
        ]

        # Mock the pybaseball pitcher stats call to raise HTTPError 403
        with (
            patch(
                "mlb_watchability.data_retrieval.pb.pitching_stats"
            ) as mock_pb_pitching,
            patch("mlb_watchability.data_retrieval.pb.team_batting") as mock_pb_team,
            patch("mlb_watchability.data_retrieval.pd.read_csv") as mock_read_csv,
        ):
            mock_pb_pitching.side_effect = requests.exceptions.HTTPError(
                "Error accessing 'https://www.fangraphs.com/leaders-legacy.aspx'. Received status code 403"
            )
            # Mock team batting to succeed so we test the pitcher stats failure
            mock_pb_team.return_value = pd.DataFrame(
                {
                    "Team": ["NYY"],
                    "Bat": [10.0],
                    "Barrel%": [0.08],
                    "BsR": [5.0],
                    "Fld": [15.0],
                    "wRC": [100],
                    "R": [90],
                }
            )
            mock_read_csv.return_value = pd.DataFrame(
                {"Team": ["NYY"], "Payroll": [200000000], "Age": [28.5]}
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                original_cwd = os.getcwd()
                try:
                    os.chdir(temp_dir)

                    # Run the CLI and expect it to exit with error code 1
                    result = self.runner.invoke(markdown_app, ["2025-07-31"])

                    assert result.exit_code == 1
                    assert "Error generating markdown file" in result.output
                    assert "403" in result.output
                    # Verify no markdown file was created
                    assert not Path("mlb_what_to_watch_2025_07_31.md").exists()

                finally:
                    os.chdir(original_cwd)

    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    def test_markdown_cli_fails_when_team_stats_raises_exception(
        self, mock_schedule: MagicMock
    ) -> None:
        """Test that markdown CLI fails fast when team stats API returns 403 error."""
        # Mock get_game_schedule to return valid games
        mock_schedule.return_value = [
            {
                "date": "2025-07-31",
                "away_team": "Atlanta Braves",
                "home_team": "Cincinnati Reds",
                "time": "19:10",
                "away_starter": "Carlos Carrasco",
                "home_starter": "Andrew Abbott",
            }
        ]

        # Mock the pybaseball team batting call to raise HTTPError 403
        with (
            patch("mlb_watchability.data_retrieval.pb.team_batting") as mock_pb_team,
            patch(
                "mlb_watchability.data_retrieval.pb.pitching_stats"
            ) as mock_pb_pitching,
            patch("mlb_watchability.data_retrieval.pd.read_csv") as mock_read_csv,
        ):
            mock_pb_team.side_effect = requests.exceptions.HTTPError(
                "Error accessing 'https://www.fangraphs.com/leaders-legacy.aspx'. Received status code 403"
            )
            # Mock pitcher stats to succeed so we test the team stats failure
            mock_pb_pitching.return_value = pd.DataFrame(
                {
                    "Name": ["Test Pitcher"],
                    "Team": ["ATL"],
                    "GS": [25],
                    "xFIP-": [100],
                    "SwStr%": [0.10],
                    "Strikes": [1000],
                    "Pitches": [1800],
                    "FBv": [92.0],
                    "Age": [28],
                    "Pace": [23.0],
                    "ERA-": [95],
                    "KN%": [0.0],
                }
            )
            mock_read_csv.return_value = pd.DataFrame(
                {"Team": ["ATL"], "Payroll": [200000000], "Age": [28.5]}
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                original_cwd = os.getcwd()
                try:
                    os.chdir(temp_dir)

                    # Run the CLI and expect it to exit with error code 1
                    result = self.runner.invoke(markdown_app, ["2025-07-31"])

                    assert result.exit_code == 1
                    assert "Error generating markdown file" in result.output
                    assert "403" in result.output
                    # Verify no markdown file was created
                    assert not Path("mlb_what_to_watch_2025_07_31.md").exists()

                finally:
                    os.chdir(original_cwd)

    @patch("mlb_watchability.markdown_cli.get_game_schedule")
    def test_markdown_cli_with_simulated_api_failure(
        self, mock_schedule: MagicMock
    ) -> None:
        """Integration test simulating API 403 failures using mocks."""
        # Mock get_game_schedule to return valid games
        mock_schedule.return_value = [
            {
                "date": "2025-07-31",
                "away_team": "Texas Rangers",
                "home_team": "Seattle Mariners",
                "time": "22:40",
                "away_starter": "Kumar Rocker",
                "home_starter": "George Kirby",
            }
        ]

        # Patch both pybaseball functions to simulate current 403 state
        with (
            patch("mlb_watchability.data_retrieval.pb.pitching_stats") as mock_pitching,
            patch("mlb_watchability.data_retrieval.pb.team_batting") as mock_batting,
            patch("mlb_watchability.data_retrieval.pd.read_csv") as mock_read_csv,
        ):

            # Both raise the actual 403 error we're seeing
            error_403 = requests.exceptions.HTTPError(
                "Error accessing 'https://www.fangraphs.com/leaders-legacy.aspx'. Received status code 403"
            )
            mock_pitching.side_effect = error_403
            mock_batting.side_effect = error_403
            mock_read_csv.return_value = pd.DataFrame(
                {"Team": ["TEX"], "Payroll": [200000000], "Age": [28.5]}
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                original_cwd = os.getcwd()
                try:
                    os.chdir(temp_dir)

                    # Test that CLI fails fast
                    result = self.runner.invoke(markdown_app, ["2025-07-31"])
                    assert result.exit_code == 1
                    assert "403" in result.output
                    # Verify no markdown file was created
                    assert not Path("mlb_what_to_watch_2025_07_31.md").exists()

                finally:
                    os.chdir(original_cwd)
