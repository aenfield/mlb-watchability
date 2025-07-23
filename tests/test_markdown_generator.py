"""Tests for markdown generation functionality."""

from unittest.mock import MagicMock, patch

from mlb_watchability.game_scores import GameScore
from mlb_watchability.markdown_generator import (
    generate_all_game_details,
    generate_complete_markdown_content,
    generate_game_detail_section,
    generate_markdown_filename,
    generate_markdown_table,
    generate_metadata_block,
    generate_pitcher_breakdown_table,
    generate_team_breakdown_table,
)
from mlb_watchability.pitcher_stats import PitcherStats
from mlb_watchability.team_stats import TeamStats


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

    def test_generate_team_breakdown_table(self) -> None:
        """Test team breakdown table generation."""
        # Create mock team stats
        team_stats = TeamStats(
            name="Los Angeles Dodgers",
            batting_runs=45.2,
            barrel_rate=0.098,
            baserunning_runs=-2.1,
            fielding_runs=12.7,
            payroll=245.8,
            age=28.4,
            luck=8.3,
        )

        # Create mock team NERD stats
        team_nerd_stats = MagicMock()
        team_nerd_stats.team_stats = team_stats
        team_nerd_stats.z_batting_runs = 1.23
        team_nerd_stats.z_barrel_rate = 0.45
        team_nerd_stats.z_baserunning_runs = -0.32
        team_nerd_stats.z_fielding_runs = 0.89
        team_nerd_stats.z_payroll = -1.45
        team_nerd_stats.z_age = -0.67
        team_nerd_stats.z_luck = 0.78
        team_nerd_stats.batting_component = 1.23
        team_nerd_stats.barrel_component = 0.45
        team_nerd_stats.baserunning_component = -0.32
        team_nerd_stats.fielding_component = 0.89
        team_nerd_stats.payroll_component = 1.45
        team_nerd_stats.age_component = 0.67
        team_nerd_stats.luck_component = 0.78
        team_nerd_stats.constant_component = 4.00
        team_nerd_stats.tnerd_score = 9.15

        result = generate_team_breakdown_table(
            "Los Angeles Dodgers", team_nerd_stats, "LAD"
        )

        # Check structure
        assert "### Los Angeles Dodgers" in result
        assert "| **Raw Stat** |" in result
        assert "| **Z-Score** |" in result
        assert "| **tNERD** |" in result

        # Check specific values
        assert "45.2" in result  # batting runs
        assert "9.8%" in result  # barrel rate as percentage
        assert "$245.8M" in result  # payroll with formatting
        assert "1.23" in result  # z-score
        assert "9.15" in result  # total tNERD score

    def test_generate_pitcher_breakdown_table(self) -> None:
        """Test pitcher breakdown table generation."""
        # Create mock pitcher stats
        pitcher_stats = PitcherStats(
            name="Gerrit Cole",
            team="NYY",
            xfip_minus=85,
            swinging_strike_rate=0.145,
            strike_rate=0.662,
            velocity=96.8,
            age=33,
            pace=19.2,
            luck=-12,
            knuckleball_rate=0.0,
        )

        # Create mock pitcher NERD stats
        pitcher_nerd_stats = MagicMock()
        pitcher_nerd_stats.pitcher_stats = pitcher_stats
        pitcher_nerd_stats.z_xfip_minus = -1.34
        pitcher_nerd_stats.z_swinging_strike_rate = 1.67
        pitcher_nerd_stats.z_strike_rate = 0.89
        pitcher_nerd_stats.z_velocity = 1.45
        pitcher_nerd_stats.z_age = 0.78
        pitcher_nerd_stats.z_pace = -0.23
        pitcher_nerd_stats.xfip_component = 2.68
        pitcher_nerd_stats.swinging_strike_component = 0.84
        pitcher_nerd_stats.strike_component = 0.45
        pitcher_nerd_stats.velocity_component = 1.45
        pitcher_nerd_stats.age_component = 0.78
        pitcher_nerd_stats.pace_component = 0.12
        pitcher_nerd_stats.luck_component = 0.0
        pitcher_nerd_stats.knuckleball_component = 0.0
        pitcher_nerd_stats.constant_component = 3.80
        pitcher_nerd_stats.pnerd_score = 10.12

        result = generate_pitcher_breakdown_table(
            "Gerrit Cole", pitcher_nerd_stats, is_home=True
        )

        # Check structure
        assert "### Home starter: Gerrit Cole" in result
        assert "| **Raw Stat** |" in result
        assert "| **Z-Score** |" in result
        assert "| **pNERD** |" in result

        # Check specific values
        assert "85" in result  # xFIP-
        assert "14.5%" in result  # SwStr% as percentage
        assert "96.8 mph" in result  # velocity with units
        assert "19.2s" in result  # pace with units
        assert "10.12" in result  # total pNERD score

        # Test visiting pitcher
        result_away = generate_pitcher_breakdown_table(
            "Gerrit Cole", pitcher_nerd_stats, is_home=False
        )
        assert "### Visiting starter: Gerrit Cole" in result_away

    def test_generate_game_detail_section(self) -> None:
        """Test game detail section generation."""
        # Create a game score
        game_score = GameScore(
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
        )

        # Create properly structured mock team stats
        away_team_stats = TeamStats(
            name="New York Yankees",
            batting_runs=52.1,
            barrel_rate=0.102,
            baserunning_runs=3.4,
            fielding_runs=15.2,
            payroll=285.6,
            age=29.1,
            luck=5.7,
        )

        home_team_stats = TeamStats(
            name="Los Angeles Dodgers",
            batting_runs=45.2,
            barrel_rate=0.098,
            baserunning_runs=-2.1,
            fielding_runs=12.7,
            payroll=245.8,
            age=28.4,
            luck=8.3,
        )

        # Create properly structured mock pitcher stats
        away_pitcher_stats = PitcherStats(
            name="Gerrit Cole",
            team="NYY",
            xfip_minus=85,
            swinging_strike_rate=0.145,
            strike_rate=0.662,
            velocity=96.8,
            age=33,
            pace=19.2,
            luck=-12,
            knuckleball_rate=0.0,
        )

        home_pitcher_stats = PitcherStats(
            name="Walker Buehler",
            team="LAD",
            xfip_minus=92,
            swinging_strike_rate=0.128,
            strike_rate=0.648,
            velocity=94.3,
            age=29,
            pace=20.1,
            luck=8,
            knuckleball_rate=0.0,
        )

        # Create mock team NERD stats with proper attributes
        away_team_nerd = MagicMock()
        away_team_nerd.team_stats = away_team_stats
        away_team_nerd.z_batting_runs = 1.5
        away_team_nerd.z_barrel_rate = 0.8
        away_team_nerd.z_baserunning_runs = 0.4
        away_team_nerd.z_fielding_runs = 1.1
        away_team_nerd.z_payroll = -1.8
        away_team_nerd.z_age = -0.3
        away_team_nerd.z_luck = 0.5
        away_team_nerd.batting_component = 1.5
        away_team_nerd.barrel_component = 0.8
        away_team_nerd.baserunning_component = 0.4
        away_team_nerd.fielding_component = 1.1
        away_team_nerd.payroll_component = 1.8
        away_team_nerd.age_component = 0.3
        away_team_nerd.luck_component = 0.5
        away_team_nerd.constant_component = 4.0
        away_team_nerd.tnerd_score = 10.4

        home_team_nerd = MagicMock()
        home_team_nerd.team_stats = home_team_stats
        home_team_nerd.z_batting_runs = 1.2
        home_team_nerd.z_barrel_rate = 0.4
        home_team_nerd.z_baserunning_runs = -0.3
        home_team_nerd.z_fielding_runs = 0.9
        home_team_nerd.z_payroll = -1.4
        home_team_nerd.z_age = -0.7
        home_team_nerd.z_luck = 0.8
        home_team_nerd.batting_component = 1.2
        home_team_nerd.barrel_component = 0.4
        home_team_nerd.baserunning_component = -0.3
        home_team_nerd.fielding_component = 0.9
        home_team_nerd.payroll_component = 1.4
        home_team_nerd.age_component = 0.7
        home_team_nerd.luck_component = 0.8
        home_team_nerd.constant_component = 4.0
        home_team_nerd.tnerd_score = 9.1

        # Create mock pitcher NERD stats with proper attributes
        away_pitcher_nerd = MagicMock()
        away_pitcher_nerd.pitcher_stats = away_pitcher_stats
        away_pitcher_nerd.z_xfip_minus = -1.3
        away_pitcher_nerd.z_swinging_strike_rate = 1.7
        away_pitcher_nerd.z_strike_rate = 0.9
        away_pitcher_nerd.z_velocity = 1.5
        away_pitcher_nerd.z_age = 0.8
        away_pitcher_nerd.z_pace = -0.2
        away_pitcher_nerd.xfip_component = 2.6
        away_pitcher_nerd.swinging_strike_component = 0.85
        away_pitcher_nerd.strike_component = 0.45
        away_pitcher_nerd.velocity_component = 1.5
        away_pitcher_nerd.age_component = 0.8
        away_pitcher_nerd.pace_component = 0.1
        away_pitcher_nerd.luck_component = 0.0
        away_pitcher_nerd.knuckleball_component = 0.0
        away_pitcher_nerd.constant_component = 3.8
        away_pitcher_nerd.pnerd_score = 10.1

        home_pitcher_nerd = MagicMock()
        home_pitcher_nerd.pitcher_stats = home_pitcher_stats
        home_pitcher_nerd.z_xfip_minus = -0.8
        home_pitcher_nerd.z_swinging_strike_rate = 0.9
        home_pitcher_nerd.z_strike_rate = 0.4
        home_pitcher_nerd.z_velocity = 0.7
        home_pitcher_nerd.z_age = -0.2
        home_pitcher_nerd.z_pace = 0.1
        home_pitcher_nerd.xfip_component = 1.6
        home_pitcher_nerd.swinging_strike_component = 0.45
        home_pitcher_nerd.strike_component = 0.2
        home_pitcher_nerd.velocity_component = 0.7
        home_pitcher_nerd.age_component = 0.2
        home_pitcher_nerd.pace_component = -0.05
        home_pitcher_nerd.luck_component = 0.4
        home_pitcher_nerd.knuckleball_component = 0.0
        home_pitcher_nerd.constant_component = 3.8
        home_pitcher_nerd.pnerd_score = 7.3

        # Create team and pitcher details dicts
        team_nerd_details = {"NYY": away_team_nerd, "LAD": home_team_nerd}
        pitcher_nerd_details = {
            "Gerrit Cole": away_pitcher_nerd,
            "Walker Buehler": home_pitcher_nerd,
        }

        result = generate_game_detail_section(
            game_score, team_nerd_details, pitcher_nerd_details
        )

        # Check section header
        assert "## New York Yankees @ Los Angeles Dodgers, 10:10p" in result

        # Check that team and pitcher names appear in the result
        assert "New York Yankees" in result
        assert "Los Angeles Dodgers" in result
        assert "Gerrit Cole" in result
        assert "Walker Buehler" in result

        # Check that the structure includes the expected sections
        assert "### New York Yankees" in result
        assert "### Los Angeles Dodgers" in result
        assert "### Visiting starter: Gerrit Cole" in result
        assert "### Home starter: Walker Buehler" in result

    def test_generate_all_game_details_sorts_by_gnerd_score(self) -> None:
        """Test that games in Detail section are sorted by gNERD score descending."""

        # Create multiple games with different gNERD scores
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
                away_team_nerd=7.0,
                home_team_nerd=8.0,
                average_team_nerd=7.5,
                away_pitcher_nerd=6.0,
                home_pitcher_nerd=7.0,
                average_pitcher_nerd=6.5,
                gnerd_score=15.0,
            ),
            GameScore(
                away_team="Team E",
                home_team="Team F",
                away_starter="Pitcher E",
                home_starter="Pitcher F",
                game_time="21:00",
                away_team_nerd=4.0,
                home_team_nerd=5.0,
                average_team_nerd=4.5,
                away_pitcher_nerd=3.0,
                home_pitcher_nerd=4.0,
                average_pitcher_nerd=3.5,
                gnerd_score=8.0,
            ),
        ]

        # Mock the detailed score functions to return empty dicts
        with (
            patch(
                "mlb_watchability.markdown_generator.calculate_detailed_team_nerd_scores"
            ) as mock_teams,
            patch(
                "mlb_watchability.markdown_generator.calculate_detailed_pitcher_nerd_scores"
            ) as mock_pitchers,
        ):

            mock_teams.return_value = {}
            mock_pitchers.return_value = {}

            result = generate_all_game_details(game_scores, "2025-07-20")

            # Check that games appear in order of gNERD score (highest first)
            # Game with score 15.0 should appear before game with score 10.0,
            # which should appear before game with score 8.0
            team_c_pos = result.find("Team C @ Team D")  # gnerd_score=15.0
            team_a_pos = result.find("Team A @ Team B")  # gnerd_score=10.0
            team_e_pos = result.find("Team E @ Team F")  # gnerd_score=8.0

            assert team_c_pos < team_a_pos < team_e_pos

            # Verify Detail header is present
            assert "# Detail" in result
