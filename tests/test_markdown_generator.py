"""Tests for markdown generation functionality."""

from mlb_watchability.game_scores import GameScore
from mlb_watchability.markdown_generator import (
    generate_complete_markdown_content,
    generate_markdown_filename,
    generate_markdown_table,
    generate_metadata_block,
)


class TestMarkdownGenerator:
    """Test cases for markdown generation functions."""

    def test_generate_metadata_block(self) -> None:
        """Test metadata block generation."""
        result = generate_metadata_block("2025-07-20")

        expected = """---
title: "MLB: What to watch on July 20, 2025"
date: 2025-07-20
tags: mlbw
---"""

        assert result == expected

    def test_generate_metadata_block_invalid_date(self) -> None:
        """Test metadata block generation with invalid date."""
        result = generate_metadata_block("invalid-date")

        # Should use the original string as fallback
        assert 'title: "MLB: What to watch on invalid-date"' in result
        assert "date: invalid-date" in result

    def test_generate_markdown_filename(self) -> None:
        """Test markdown filename generation."""
        result = generate_markdown_filename("2025-07-20")
        assert result == "mlb_what_to_watch_2025_07_20.md"

        result = generate_markdown_filename("2024-12-31")
        assert result == "mlb_what_to_watch_2024_12_31.md"

    def test_generate_markdown_table_with_complete_data(self) -> None:
        """Test markdown table generation with complete game data."""
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

        result = generate_markdown_table(game_scores)

        # Check that wideTable tags are present
        assert result.startswith("{% wideTable %}")
        assert result.endswith("{% endwideTable %}")

        # Check that the table header is present with correct format
        assert (
            "| Score | Time (EDT) | Visitors | Score | Home | Score | Starter (V) | Score | Starter (H) | Score |"
            in result
        )
        assert (
            "|-------|------------|----------|-------|------|-------|-------------|-------|-------------|-------|"
            in result
        )

        # Check that both games are present with their gNERD scores
        assert "15.1" in result  # Higher gNERD score
        assert "13.5" in result  # Lower gNERD score

        # Check content includes team names and NERD scores
        assert "New York Yankees" in result
        assert "Los Angeles Dodgers" in result
        assert "Boston Red Sox" in result
        assert "Chicago Cubs" in result

        # Check pitcher names are present
        assert "Gerrit Cole" in result
        assert "Walker Buehler" in result
        assert "Brayan Bello" in result
        assert "Shota Imanaga" in result

        # Check team NERD scores are present
        assert "8.2" in result  # Yankees team score
        assert "7.9" in result  # Dodgers team score
        assert "6.8" in result  # Red Sox team score
        assert "9.5" in result  # Cubs team score

        # Check pitcher NERD scores are present
        assert "7.8" in result  # Gerrit Cole score
        assert "6.2" in result  # Walker Buehler score
        assert "3.9" in result  # Brayan Bello score
        assert "6.7" in result  # Shota Imanaga score

    def test_generate_markdown_table_with_missing_data(self) -> None:
        """Test markdown table generation with missing pitcher data."""
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

        result = generate_markdown_table(game_scores)

        # Check that wideTable tags are present
        assert result.startswith("{% wideTable %}")
        assert result.endswith("{% endwideTable %}")

        # Check that TBD pitcher shows without score
        assert "TBD" in result
        assert "No data" in result
        assert "Logan Gilbert" in result
        assert "5.8" in result

        # Check team names are present
        assert "San Francisco Giants" in result
        assert "Seattle Mariners" in result

        # Check team NERD scores are present
        assert "5.2" in result  # Giants team score
        assert "7.1" in result  # Mariners team score

    def test_generate_markdown_table_empty_list(self) -> None:
        """Test markdown table generation with empty game list."""
        result = generate_markdown_table([])
        assert result == "No games available for table."

    def test_generate_complete_markdown_content(self) -> None:
        """Test complete markdown content generation."""
        game_scores = [
            GameScore(
                away_team="Test Team A",
                home_team="Test Team B",
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
            )
        ]

        result = generate_complete_markdown_content("2025-07-20", game_scores)

        # Check that all parts are present
        assert "---" in result  # Metadata block
        assert 'title: "MLB: What to watch on July 20, 2025"' in result
        assert "date: 2025-07-20" in result
        assert "tags: mlbw" in result
        assert "| Score | Time (EDT)" in result  # Table header
        assert "Test Team A" in result

        # Check structure - metadata should be at top, footer at bottom
        lines = result.split("\n")
        assert lines[0] == "---"  # Metadata starts

    def test_generate_complete_markdown_content_empty_games(self) -> None:
        """Test complete markdown content generation with no games."""
        result = generate_complete_markdown_content("2025-07-20", [])

        # Should still have metadata and structure, but table shows no games
        assert "---" in result
        assert "No games available for table." in result
