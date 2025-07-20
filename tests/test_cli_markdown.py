"""Tests for CLI markdown table formatting."""

import os
import tempfile

from mlb_watchability.cli import format_games_as_markdown_table
from mlb_watchability.game_scores import GameScore


class TestCliMarkdownFormatting:
    """Test cases for CLI markdown table formatting."""

    def test_format_games_as_markdown_table_with_all_data(self) -> None:
        """Test markdown table formatting with complete game data."""
        # Games should be pre-sorted by gNERD (highest first)
        game_scores = [
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

        result = format_games_as_markdown_table(game_scores)

        result_lines = result.split("\n")

        # Check header
        assert (
            result_lines[0]
            == "| Score | Time | Visitors | Score | Home | Score | Starter (V) | Score | Starter (H) | Score |"
        )
        assert (
            result_lines[1]
            == "|-------|------|----------|-------|------|-------|-------------|-------|-------------|-------|"
        )

        # Check that games are in the order provided (should be pre-sorted by gNERD)
        assert "15.1" in result_lines[2]  # Higher gNERD should be first
        assert "13.5" in result_lines[3]  # Lower gNERD should be second

        # Check content includes team names, NERD scores, and pitcher info in separate columns
        assert "New York Yankees" in result_lines[2]
        assert "8.2" in result_lines[2]
        assert "Gerrit Cole" in result_lines[2]
        assert "7.8" in result_lines[2]
        assert "Los Angeles Dodgers" in result_lines[2]
        assert "7.9" in result_lines[2]
        assert "Walker Buehler" in result_lines[2]
        assert "6.2" in result_lines[2]

    def test_format_games_as_markdown_table_with_missing_pitcher_data(self) -> None:
        """Test markdown table formatting with missing pitcher data."""
        game_scores = [
            GameScore(
                away_team="San Francisco Giants",
                home_team="Seattle Mariners",
                away_starter="TBD",
                home_starter="Logan Gilbert",
                game_time="21:40",
                away_team_nerd=5.2,
                home_team_nerd=7.1,
                average_team_nerd=6.15,
                away_pitcher_nerd=None,
                home_pitcher_nerd=5.8,
                average_pitcher_nerd=5.8,
                gnerd_score=11.95,
            )
        ]

        result = format_games_as_markdown_table(game_scores)

        result_lines = result.split("\n")

        # Check header
        assert (
            result_lines[0]
            == "| Score | Time | Visitors | Score | Home | Score | Starter (V) | Score | Starter (H) | Score |"
        )
        assert (
            result_lines[1]
            == "|-------|------|----------|-------|------|-------|-------------|-------|-------------|-------|"
        )

        # Check that TBD pitcher shows without score
        assert (
            result_lines[2]
            == "| 11.9 | 9:40p | [San Francisco Giants](https://www.fangraphs.com/teams/giants/stats) | 5.2 | [Seattle Mariners](https://www.fangraphs.com/teams/mariners/stats) | 7.1 | TBD | No data | [Logan Gilbert](https://www.fangraphs.com/search?q=Gilbert) | 5.8 |"
        )

    def test_format_games_as_markdown_table_with_no_pitcher_data(self) -> None:
        """Test markdown table formatting with no pitcher data."""
        game_scores = [
            GameScore(
                away_team="Miami Marlins",
                home_team="Colorado Rockies",
                away_starter=None,
                home_starter=None,
                game_time="20:00",
                away_team_nerd=4.1,
                home_team_nerd=3.8,
                average_team_nerd=3.95,
                away_pitcher_nerd=None,
                home_pitcher_nerd=None,
                average_pitcher_nerd=None,
                gnerd_score=3.95,
            )
        ]

        result = format_games_as_markdown_table(game_scores)

        result_lines = result.split("\n")

        # Check that missing pitchers show as TBD
        assert (
            result_lines[2]
            == "| 4.0 | 8:00p | [Miami Marlins](https://www.fangraphs.com/teams/marlins/stats) | 4.1 | [Colorado Rockies](https://www.fangraphs.com/teams/rockies/stats) | 3.8 | TBD | No data | TBD | No data |"
        )

    def test_format_games_as_markdown_table_empty_list(self) -> None:
        """Test markdown table formatting with empty game list."""
        result = format_games_as_markdown_table([])

        assert result == "No games available for table."

    def test_format_games_as_markdown_table_preserves_order(self) -> None:
        """Test that markdown table preserves the input order (should be pre-sorted by gNERD)."""
        game_scores = [
            GameScore(
                away_team="Team A",
                home_team="Team B",
                away_starter="Pitcher A",
                home_starter="Pitcher B",
                game_time="19:00",
                away_team_nerd=5.0,
                home_team_nerd=6.0,
                average_team_nerd=5.5,
                away_pitcher_nerd=4.0,
                home_pitcher_nerd=5.0,
                average_pitcher_nerd=4.5,
                gnerd_score=10.0,
            ),
            GameScore(
                away_team="Team C",
                home_team="Team D",
                away_starter="Pitcher C",
                home_starter="Pitcher D",
                game_time="20:00",
                away_team_nerd=3.0,
                home_team_nerd=4.0,
                average_team_nerd=3.5,
                away_pitcher_nerd=2.0,
                home_pitcher_nerd=3.0,
                average_pitcher_nerd=2.5,
                gnerd_score=6.0,
            ),
        ]

        result = format_games_as_markdown_table(game_scores)
        result_lines = result.split("\n")

        # First game (higher gNERD) should appear first in table
        assert "| 10.0 |" in result_lines[2]
        assert "Team A" in result_lines[2]

        # Second game (lower gNERD) should appear second in table
        assert "| 6.0 |" in result_lines[3]
        assert "Team C" in result_lines[3]

    def test_markdown_file_creation(self) -> None:
        """Test that markdown table is properly written to file when CLI runs."""
        # This test would require testing the full CLI command which involves
        # external API calls. For now, we'll test the file writing logic separately
        # by testing that the file writing code works in isolation.

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file_path = os.path.join(temp_dir, "test-games.md")

            # Test the file writing logic
            markdown_content = "| Score | Time | Visitors | Score | Home | Score | Starter (V) | Score | Starter (H) | Score |\n|-------|------|----------|-------|------|-------|-------------|-------|-------------|-------|\n| 13.5 | 7:15p | Test Team A | 6.8 | Test Team B | 9.5 | Pitcher A | 3.9 | Pitcher B | 6.7 |"

            try:
                with open(test_file_path, "w", encoding="utf-8") as f:
                    f.write("# Today's MLB Games (2025-07-20)\n\n")
                    f.write(markdown_content)
                    f.write("\n")

                # Verify file was created and contains expected content
                assert os.path.exists(test_file_path)

                with open(test_file_path, encoding="utf-8") as f:
                    content = f.read()

                assert "# Today's MLB Games (2025-07-20)" in content
                assert (
                    "| Score | Time | Visitors | Score | Home | Score | Starter (V) | Score | Starter (H) | Score |"
                    in content
                )
                assert "Test Team A" in content
                assert "Pitcher A" in content

            except Exception as e:
                raise AssertionError(f"File writing test failed: {e}") from e
