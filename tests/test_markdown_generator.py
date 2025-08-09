"""Tests for markdown generation functionality."""

from unittest.mock import MagicMock

from mlb_watchability.game_scores import GameScore
from mlb_watchability.markdown_generator import (
    generate_all_game_details,
    generate_automatic_anchor_id,
    generate_complete_markdown_content,
    generate_game_detail_section,
    generate_markdown_filename,
    generate_markdown_table,
    generate_metadata_block,
    generate_pitcher_breakdown_table,
    generate_team_breakdown_table,
)
from mlb_watchability.pitcher_stats import PitcherNerdStats, PitcherStats
from mlb_watchability.team_stats import TeamNerdStats, TeamStats


class TestMarkdownGenerator:
    """Test cases for markdown generation functions."""

    def create_minimal_stats(
        self,
    ) -> tuple[dict[str, TeamNerdStats], dict[str, PitcherNerdStats]]:
        """Create minimal test data for team and pitcher stats."""
        team_nerd_details = {
            "TST": TeamNerdStats(
                team_stats=TeamStats(
                    name="TST",
                    batting_runs=5.0,
                    barrel_rate=0.08,
                    baserunning_runs=2.0,
                    fielding_runs=5.0,
                    payroll=180.0,
                    age=28.0,
                    luck=3.0,
                ),
                z_batting_runs=0.5,
                z_barrel_rate=0.2,
                z_baserunning_runs=0.1,
                z_fielding_runs=0.5,
                z_payroll=-0.3,
                z_age=-0.5,
                z_luck=0.1,
                adjusted_payroll=0.3,
                adjusted_age=0.5,
                adjusted_luck=0.1,
                tnerd_score=5.0,
            )
        }

        pitcher_nerd_details = {
            "Test Pitcher": PitcherNerdStats(
                pitcher_stats=PitcherStats(
                    name="Test Pitcher",
                    team="TST",
                    xfip_minus=95.0,
                    swinging_strike_rate=0.12,
                    strike_rate=0.65,
                    velocity=94.0,
                    age=28,
                    pace=21.0,
                    luck=5.0,
                    knuckleball_rate=0.0,
                ),
                z_xfip_minus=-0.5,
                z_swinging_strike_rate=1.0,
                z_strike_rate=0.5,
                z_velocity=0.5,
                z_age=-0.2,
                z_pace=-0.3,
                adjusted_velocity=0.5,
                adjusted_age=0.2,
                adjusted_luck=0.25,
                pnerd_score=7.0,
            )
        }

        return team_nerd_details, pitcher_nerd_details

    def test_generate_metadata_block(self) -> None:
        """Test metadata block generation."""
        result = generate_metadata_block("2025-07-20")

        expected = """---
title: "MLB: What to watch on July 20, 2025"
date: 2025-07-20
tags: mlbw
---"""

        assert result == expected

    def test_generate_metadata_block_single_digit_day(self) -> None:
        """Test metadata block generation with single-digit day (no leading zero)."""
        result = generate_metadata_block("2025-08-01")

        expected = """---
title: "MLB: What to watch on August 1, 2025"
date: 2025-08-01
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

    def test_generate_automatic_anchor_id(self) -> None:
        """Test automatic anchor ID generation from heading text."""
        # Test basic team names
        assert generate_automatic_anchor_id("Houston Astros") == "houston-astros"
        assert generate_automatic_anchor_id("New York Yankees") == "new-york-yankees"
        assert (
            generate_automatic_anchor_id("Los Angeles Dodgers") == "los-angeles-dodgers"
        )

        # Test game headings with times
        assert (
            generate_automatic_anchor_id("Houston Astros @ Arizona Diamondbacks, 3:40p")
            == "houston-astros-arizona-diamondbacks-3-40p"
        )
        assert (
            generate_automatic_anchor_id("Milwaukee Brewers @ Seattle Mariners, 3:40p")
            == "milwaukee-brewers-seattle-mariners-3-40p"
        )

        # Test pitcher headings
        assert (
            generate_automatic_anchor_id("Brandon Walter, Houston Astros")
            == "brandon-walter-houston-astros"
        )
        assert (
            generate_automatic_anchor_id("Brandon Pfaadt, Arizona Diamondbacks")
            == "brandon-pfaadt-arizona-diamondbacks"
        )
        assert (
            generate_automatic_anchor_id("Jesús Luzardo, Miami Marlins")
            == "jesus-luzardo-miami-marlins"
        )

        # Test special characters and multiple spaces
        assert (
            generate_automatic_anchor_id("Team with   multiple    spaces")
            == "team-with-multiple-spaces"
        )
        assert generate_automatic_anchor_id("Team @ Home, 12:30p") == "team-home-12-30p"
        assert (
            generate_automatic_anchor_id("Team-Name & Other/Team")
            == "team-name-other-team"
        )

        # Test edge cases
        assert generate_automatic_anchor_id("") == ""
        assert generate_automatic_anchor_id("   ") == ""
        assert generate_automatic_anchor_id("---") == ""
        assert generate_automatic_anchor_id("Team---Name") == "team-name"

        # Test case conversion
        assert generate_automatic_anchor_id("UPPERCASE TEAM") == "uppercase-team"
        assert generate_automatic_anchor_id("MiXeD cAsE") == "mixed-case"

        # Test accented character normalization
        assert generate_automatic_anchor_id("José Altuve") == "jose-altuve"
        assert generate_automatic_anchor_id("Jesús Luzardo") == "jesus-luzardo"
        assert generate_automatic_anchor_id("Andrés Giménez") == "andres-gimenez"
        assert generate_automatic_anchor_id("Gleyber Torres") == "gleyber-torres"
        assert (
            generate_automatic_anchor_id("José Berríos, Toronto Blue Jays")
            == "jose-berrios-toronto-blue-jays"
        )
        assert (
            generate_automatic_anchor_id("Cristian Javier, Houston Astros")
            == "cristian-javier-houston-astros"
        )

        # Test various accented characters
        assert generate_automatic_anchor_id("àáâãäåæçèéêë") == "aaaaaaaeceeee"
        assert generate_automatic_anchor_id("ìíîïñòóôõöøùúûü") == "iiiinoooooouuuu"
        assert generate_automatic_anchor_id("ýÿ") == "yy"

    def test_generate_markdown_table_with_complete_data(self) -> None:
        """Test markdown table generation with complete game data."""
        team_nerd_details, pitcher_nerd_details = self.create_minimal_stats()

        game_scores = [
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
            ),
        ]

        result = generate_markdown_table(game_scores)

        # Check that wideTable tags are present
        assert result.startswith("{% wideTable %}")
        assert result.endswith("{% endwideTable %}")

        # Check that the table header is present with correct format
        assert (
            "| Score | Time (PT) | Visitors | Score | Home | Score | Starter (V) | Score | Starter (H) | Score |"
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

        # Check that markdown-it-attrs syntax is used for time values (now PT times)
        assert "7:10p {data-sort='1910'}" in result
        assert "4:15p {data-sort='1615'}" in result

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

    def test_generate_markdown_table_anchor_links(self) -> None:
        """Test that table anchor links match automatic anchor generation."""
        team_nerd_details, pitcher_nerd_details = self.create_minimal_stats()

        game_scores = [
            GameScore(
                away_team="Houston Astros",
                home_team="Arizona Diamondbacks",
                away_starter="Brandon Walter",
                home_starter="Brandon Pfaadt",
                game_time="15:40",
                game_date="2025-07-27",  # 3:40p
                away_team_nerd_score=4.9,
                home_team_nerd_score=7.9,
                average_team_nerd_score=6.4,
                away_pitcher_nerd_score=8.9,
                home_pitcher_nerd_score=4.4,
                average_pitcher_nerd_score=6.65,
                gnerd_score=13.1,
                away_team_nerd_stats=None,
                home_team_nerd_stats=None,
                away_pitcher_nerd_stats=None,
                home_pitcher_nerd_stats=None,
            )
        ]

        result = generate_markdown_table(game_scores)

        # Check that table contains correct anchor links that match automatic generation
        # Game link: "Houston Astros @ Arizona Diamondbacks, 3:40p" -> "houston-astros-arizona-diamondbacks-3-40p"
        assert "[13.1](#houston-astros-arizona-diamondbacks-3-40p)" in result

        # Team links: team names -> lowercase with hyphens
        assert "[4.9](#houston-astros)" in result
        assert "[7.9](#arizona-diamondbacks)" in result

        # Pitcher links: "Name, Team"
        assert "[8.9](#brandon-walter-houston-astros)" in result
        assert "[4.4](#brandon-pfaadt-arizona-diamondbacks)" in result

    def test_generate_markdown_table_with_missing_data(self) -> None:
        """Test markdown table generation with missing pitcher data."""
        team_nerd_details, pitcher_nerd_details = self.create_minimal_stats()

        game_scores = [
            GameScore(
                away_team="San Francisco Giants",
                home_team="Seattle Mariners",
                away_starter="TBD",
                home_starter="Logan Gilbert",
                game_time="21:40",
                game_date="2025-07-27",
                away_team_nerd_score=5.2,
                home_team_nerd_score=7.1,
                average_team_nerd_score=6.15,
                away_pitcher_nerd_score=None,
                home_pitcher_nerd_score=5.8,
                average_pitcher_nerd_score=5.8,
                gnerd_score=11.95,
                away_team_nerd_stats=None,
                home_team_nerd_stats=None,
                away_pitcher_nerd_stats=None,
                home_pitcher_nerd_stats=None,
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
        team_nerd_details, pitcher_nerd_details = self.create_minimal_stats()

        game_scores = [
            GameScore(
                away_team="Test Team A",
                home_team="Test Team B",
                away_starter="Pitcher A",
                home_starter="Pitcher B",
                game_time="19:00",
                game_date="2025-07-27",
                away_team_nerd_score=5.0,
                home_team_nerd_score=6.0,
                average_team_nerd_score=5.5,
                away_pitcher_nerd_score=4.0,
                home_pitcher_nerd_score=5.0,
                average_pitcher_nerd_score=4.5,
                gnerd_score=10.0,
                away_team_nerd_stats=None,
                home_team_nerd_stats=None,
                away_pitcher_nerd_stats=None,
                home_pitcher_nerd_stats=None,
            )
        ]

        result = generate_complete_markdown_content("2025-07-20", game_scores)

        # Check that all parts are present
        assert "---" in result  # Metadata block
        assert 'title: "MLB: What to watch on July 20, 2025"' in result
        assert "date: 2025-07-20" in result
        assert "tags: mlbw" in result
        assert "| Score | Time (PT)" in result  # Table header
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
        assert "{% wideTable %}" in result
        assert "{% endwideTable %}" in result
        assert "| **Raw stat** |" in result
        assert "| **Z-score** |" in result
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
            "Gerrit Cole", pitcher_nerd_stats, "New York Yankees"
        )

        # Check structure
        assert "### Gerrit Cole, New York Yankees" in result
        assert "{% wideTable %}" in result
        assert "{% endwideTable %}" in result
        assert "| **Raw stat** |" in result
        assert "| **Z-score** |" in result
        assert "| **pNERD** |" in result

        # Check specific values
        assert "85" in result  # xFIP-
        assert "14.5%" in result  # SwStr% as percentage
        assert "96.8 mph" in result  # velocity with units
        assert "19.2s" in result  # pace with units
        assert "10.12" in result  # total pNERD score

        # Test visiting pitcher
        result_away = generate_pitcher_breakdown_table(
            "Gerrit Cole", pitcher_nerd_stats, "New York Yankees"
        )
        assert "### Gerrit Cole, New York Yankees" in result_away

    def test_generate_game_detail_section(self) -> None:
        """Test game detail section generation."""

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

        # Create a game score with the detailed stats
        game_score = GameScore(
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
            away_team_nerd_stats=away_team_nerd,
            home_team_nerd_stats=home_team_nerd,
            away_pitcher_nerd_stats=away_pitcher_nerd,
            home_pitcher_nerd_stats=home_pitcher_nerd,
        )

        result = generate_game_detail_section(game_score)

        # Check section header
        assert "## New York Yankees @ Los Angeles Dodgers, 7:10p" in result

        # Check that team and pitcher names appear in the result
        assert "New York Yankees" in result
        assert "Los Angeles Dodgers" in result
        assert "Gerrit Cole" in result
        assert "Walker Buehler" in result

        # Check that the structure includes the expected sections
        assert "### New York Yankees" in result
        assert "### Los Angeles Dodgers" in result
        assert "### Gerrit Cole, New York Yankees" in result
        assert "### Walker Buehler, Los Angeles Dodgers" in result

        assert "[Go back to top of page](#)" in result

    def test_generate_game_detail_section_with_missing_pitcher_data(self) -> None:
        """Test game detail section generation with missing pitcher data."""
        # Create minimal team stats and NERD stats for the test
        away_team_stats = TeamStats(
            name="Boston Red Sox",
            batting_runs=30.0,
            barrel_rate=0.095,
            baserunning_runs=2.1,
            fielding_runs=8.5,
            payroll=195.2,
            age=28.7,
            luck=3.2,
        )

        home_team_stats = TeamStats(
            name="Tampa Bay Rays",
            batting_runs=22.8,
            barrel_rate=0.088,
            baserunning_runs=-1.4,
            fielding_runs=12.1,
            payroll=125.4,
            age=27.9,
            luck=-2.7,
        )

        away_team_nerd = MagicMock()
        away_team_nerd.team_stats = away_team_stats
        away_team_nerd.z_batting_runs = 0.8
        away_team_nerd.z_barrel_rate = 0.3
        away_team_nerd.z_baserunning_runs = 0.5
        away_team_nerd.z_fielding_runs = 0.7
        away_team_nerd.z_payroll = -0.2
        away_team_nerd.z_age = 0.1
        away_team_nerd.z_luck = 0.3
        away_team_nerd.batting_component = 0.8
        away_team_nerd.barrel_component = 0.3
        away_team_nerd.baserunning_component = 0.5
        away_team_nerd.fielding_component = 0.7
        away_team_nerd.payroll_component = 0.2
        away_team_nerd.age_component = 0.0
        away_team_nerd.luck_component = 0.3
        away_team_nerd.constant_component = 4.0
        away_team_nerd.tnerd_score = 6.8

        home_team_nerd = MagicMock()
        home_team_nerd.team_stats = home_team_stats
        home_team_nerd.z_batting_runs = 0.5
        home_team_nerd.z_barrel_rate = 0.1
        home_team_nerd.z_baserunning_runs = -0.3
        home_team_nerd.z_fielding_runs = 0.9
        home_team_nerd.z_payroll = 0.8
        home_team_nerd.z_age = -0.2
        home_team_nerd.z_luck = -0.2
        home_team_nerd.batting_component = 0.5
        home_team_nerd.barrel_component = 0.1
        home_team_nerd.baserunning_component = -0.3
        home_team_nerd.fielding_component = 0.9
        home_team_nerd.payroll_component = 0.8
        home_team_nerd.age_component = 0.2
        home_team_nerd.luck_component = 0.0
        home_team_nerd.constant_component = 4.0
        home_team_nerd.tnerd_score = 6.2

        # Create pitcher stats for home pitcher (who has data)
        home_pitcher_stats = PitcherStats(
            name="Shane Baz",
            team="TB",
            xfip_minus=88,
            swinging_strike_rate=0.115,
            strike_rate=0.645,
            velocity=95.2,
            age=26,
            pace=18.8,
            luck=2,
            knuckleball_rate=0.0,
        )

        home_pitcher_nerd = MagicMock()
        home_pitcher_nerd.pitcher_stats = home_pitcher_stats
        home_pitcher_nerd.z_xfip_minus = -0.8
        home_pitcher_nerd.z_swinging_strike_rate = 0.5
        home_pitcher_nerd.z_strike_rate = 0.2
        home_pitcher_nerd.z_velocity = 0.6
        home_pitcher_nerd.z_age = -0.3
        home_pitcher_nerd.z_pace = -0.1
        home_pitcher_nerd.xfip_component = 1.6
        home_pitcher_nerd.swinging_strike_component = 0.25
        home_pitcher_nerd.strike_component = 0.1
        home_pitcher_nerd.velocity_component = 0.6
        home_pitcher_nerd.age_component = 0.3
        home_pitcher_nerd.pace_component = 0.05
        home_pitcher_nerd.luck_component = 0.05
        home_pitcher_nerd.knuckleball_component = 0.0
        home_pitcher_nerd.constant_component = 3.8
        home_pitcher_nerd.pnerd_score = 6.7

        # Create a game score with missing pitcher data
        game_score = GameScore(
            away_team="Boston Red Sox",
            home_team="Tampa Bay Rays",
            away_starter="Nick Pivetta",
            home_starter="Shane Baz",
            game_time="19:10",
            game_date="2025-07-27",
            away_team_nerd_score=6.5,
            home_team_nerd_score=5.8,
            average_team_nerd_score=6.15,
            away_pitcher_nerd_score=None,  # No data for away pitcher
            home_pitcher_nerd_score=4.2,  # Home pitcher has data
            average_pitcher_nerd_score=4.2,
            gnerd_score=10.35,
            away_team_nerd_stats=away_team_nerd,
            home_team_nerd_stats=home_team_nerd,
            away_pitcher_nerd_stats=None,  # No stats for away pitcher
            home_pitcher_nerd_stats=home_pitcher_nerd,  # Home pitcher has proper stats
        )

        result = generate_game_detail_section(game_score)

        # Check that both pitcher sections are present
        assert "### Nick Pivetta, Boston Red Sox" in result
        assert "### Shane Baz, Tampa Bay Rays" in result

        # Check that the missing pitcher shows "No detailed stats available"
        assert "No detailed stats available" in result

        # Verify the structure - "No detailed stats available" should come after the visiting starter heading
        nick_pivetta_index = result.find("### Nick Pivetta, Boston Red Sox")
        shane_baz_index = result.find("### Shane Baz, Tampa Bay Rays")
        no_data_index = result.find("No detailed stats available")

        assert nick_pivetta_index < no_data_index < shane_baz_index

    def test_generate_all_game_details_sorts_by_gnerd_score(self) -> None:
        """Test that games in Detail section are sorted by gNERD score descending."""
        team_nerd_details, pitcher_nerd_details = self.create_minimal_stats()

        # Create multiple games with different gNERD scores
        game_scores = [
            GameScore(
                away_team="Team A",
                home_team="Team B",
                away_starter="Pitcher A",
                home_starter="Pitcher B",
                game_time="19:00",
                game_date="2025-07-27",
                away_team_nerd_score=5.0,
                home_team_nerd_score=6.0,
                average_team_nerd_score=5.5,
                away_pitcher_nerd_score=4.0,
                home_pitcher_nerd_score=5.0,
                average_pitcher_nerd_score=4.5,
                gnerd_score=10.0,
                away_team_nerd_stats=None,
                home_team_nerd_stats=None,
                away_pitcher_nerd_stats=None,
                home_pitcher_nerd_stats=None,
            ),
            GameScore(
                away_team="Team C",
                home_team="Team D",
                away_starter="Pitcher C",
                home_starter="Pitcher D",
                game_time="20:00",
                game_date="2025-07-27",
                away_team_nerd_score=7.0,
                home_team_nerd_score=8.0,
                average_team_nerd_score=7.5,
                away_pitcher_nerd_score=6.0,
                home_pitcher_nerd_score=7.0,
                average_pitcher_nerd_score=6.5,
                gnerd_score=15.0,
                away_team_nerd_stats=None,
                home_team_nerd_stats=None,
                away_pitcher_nerd_stats=None,
                home_pitcher_nerd_stats=None,
            ),
            GameScore(
                away_team="Team E",
                home_team="Team F",
                away_starter="Pitcher E",
                home_starter="Pitcher F",
                game_time="21:00",
                game_date="2025-07-27",
                away_team_nerd_score=4.0,
                home_team_nerd_score=5.0,
                average_team_nerd_score=4.5,
                away_pitcher_nerd_score=3.0,
                home_pitcher_nerd_score=4.0,
                average_pitcher_nerd_score=3.5,
                gnerd_score=8.0,
                away_team_nerd_stats=None,
                home_team_nerd_stats=None,
                away_pitcher_nerd_stats=None,
                home_pitcher_nerd_stats=None,
            ),
        ]

        # No need to mock the detailed score functions since they're no longer called
        result = generate_all_game_details(game_scores)

        # Check that games appear in order of gNERD score (highest first)
        # Game with score 15.0 should appear before game with score 10.0,
        # which should appear before game with score 8.0
        team_c_pos = result.find("Team C @ Team D")  # gnerd_score=15.0
        team_a_pos = result.find("Team A @ Team B")  # gnerd_score=10.0
        team_e_pos = result.find("Team E @ Team F")  # gnerd_score=8.0

        assert team_c_pos < team_a_pos < team_e_pos

        # Verify Detail header is present
        assert "# Detail" in result

    def test_generate_game_detail_section_with_description_and_sources(self) -> None:
        """Test game detail section with game description and web sources."""
        team_nerd_details, pitcher_nerd_details = self.create_minimal_stats()

        # Create a game score with description and sources
        game_score = GameScore(
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
            game_description="This is an exciting matchup between two powerhouse teams.",
            game_description_sources=[
                {"url": "https://example.com/article1", "title": "Game Preview"},
                {"url": "https://example.com/article2", "title": "Team Analysis"},
            ],
        )

        result = generate_game_detail_section(game_score, include_descriptions=True)

        # Check that description section is present
        assert "### Summary" in result
        assert "This is an exciting matchup between two powerhouse teams." in result

        # Check that sources are formatted in single parenthetical with numbered links
        expected_attribution = "(An unable to be specified model (despite best intentions) generated this text using instructions, the NERD scores, and these sources: [1](https://example.com/article1), [2](https://example.com/article2).)"
        assert expected_attribution in result

        # Verify old multi-line format is not present
        assert "Sources:" not in result
        assert "- [Game Preview]" not in result
        assert "- [Team Analysis]" not in result
        assert "(This summary is generated by AI.)" not in result

    def test_generate_game_detail_section_with_description_no_sources(self) -> None:
        """Test game detail section with game description but no web sources."""
        team_nerd_details, pitcher_nerd_details = self.create_minimal_stats()

        # Create a game score with description but no sources
        game_score = GameScore(
            away_team="Boston Red Sox",
            home_team="Toronto Blue Jays",
            away_starter="Brayan Bello",
            home_starter="Kevin Gausman",
            game_time="19:07",
            game_date="2025-07-27",
            away_team_nerd_score=6.5,
            home_team_nerd_score=7.2,
            average_team_nerd_score=6.85,
            away_pitcher_nerd_score=5.1,
            home_pitcher_nerd_score=6.8,
            average_pitcher_nerd_score=5.95,
            gnerd_score=12.8,
            away_team_nerd_stats=None,
            home_team_nerd_stats=None,
            away_pitcher_nerd_stats=None,
            home_pitcher_nerd_stats=None,
            game_description="A competitive divisional matchup.",
            game_description_sources=[],  # Empty sources list
        )

        result = generate_game_detail_section(game_score, include_descriptions=True)

        # Check that description section is present
        assert "### Summary" in result
        assert "A competitive divisional matchup." in result

        # Check that attribution shows no sources in parenthetical format
        expected_attribution = "(An unable to be specified model (despite best intentions) generated this text using instructions and the NERD scores.)"
        assert expected_attribution in result

        # Verify old separate AI disclaimer is not present
        assert "(This summary is generated by AI.)" not in result

    def test_generate_game_detail_section_with_description_sources_no_url(self) -> None:
        """Test game detail section with sources that have no URL."""
        team_nerd_details, pitcher_nerd_details = self.create_minimal_stats()

        # Create a game score with sources missing URLs
        game_score = GameScore(
            away_team="Chicago Cubs",
            home_team="Milwaukee Brewers",
            away_starter="Shota Imanaga",
            home_starter="Freddy Peralta",
            game_time="20:10",
            game_date="2025-07-27",
            away_team_nerd_score=7.1,
            home_team_nerd_score=6.9,
            average_team_nerd_score=7.0,
            away_pitcher_nerd_score=6.2,
            home_pitcher_nerd_score=7.5,
            average_pitcher_nerd_score=6.85,
            gnerd_score=13.85,
            away_team_nerd_stats=None,
            home_team_nerd_stats=None,
            away_pitcher_nerd_stats=None,
            home_pitcher_nerd_stats=None,
            game_description="An NL Central showdown.",
            game_description_sources=[
                {"title": "Article Without URL"},  # No URL field
                {"url": "https://example.com/article2", "title": "Article With URL"},
            ],
        )

        result = generate_game_detail_section(game_score, include_descriptions=True)

        # Check that attribution handles mixed sources correctly in parenthetical format
        expected_attribution = "(An unable to be specified model (despite best intentions) generated this text using instructions, the NERD scores, and these sources: 1, [2](https://example.com/article2).)"
        assert expected_attribution in result

        # Verify old separate AI disclaimer is not present
        assert "(This summary is generated by AI.)" not in result

    def test_generate_game_detail_section_with_anthropic_provider(self) -> None:
        """Test game detail section shows Anthropic attribution for anthropic provider."""
        team_nerd_details, pitcher_nerd_details = self.create_minimal_stats()

        game_score = GameScore(
            away_team="New York Yankees",
            home_team="Los Angeles Dodgers",
            away_starter="Gerrit Cole",
            home_starter="Walker Buehler",
            game_time="19:10",
            game_date="2025-07-20",
            away_team_nerd_score=6.2,
            home_team_nerd_score=7.1,
            average_team_nerd_score=6.65,
            away_pitcher_nerd_score=8.5,
            home_pitcher_nerd_score=7.8,
            average_pitcher_nerd_score=8.15,
            gnerd_score=14.8,
            away_team_nerd_stats=team_nerd_details["TST"],
            home_team_nerd_stats=team_nerd_details["TST"],
            away_pitcher_nerd_stats=pitcher_nerd_details["Test Pitcher"],
            home_pitcher_nerd_stats=pitcher_nerd_details["Test Pitcher"],
            game_description="This is a test game description.",
            game_description_sources=[],
            game_description_provider="anthropic",
        )

        result = generate_game_detail_section(game_score, include_descriptions=True)

        # Check that Anthropic attribution is used
        expected_attribution = "(A model from [Anthropic](https://www.anthropic.com) generated this text using instructions and the NERD scores.)"
        assert expected_attribution in result

        # Verify old Claude attribution is not present
        assert "Claude](https://www.anthropic.com/claude)" not in result

    def test_generate_game_detail_section_with_openai_provider(self) -> None:
        """Test game detail section shows OpenAI attribution for openai provider."""
        team_nerd_details, pitcher_nerd_details = self.create_minimal_stats()

        game_score = GameScore(
            away_team="Boston Red Sox",
            home_team="Tampa Bay Rays",
            away_starter="Brayan Bello",
            home_starter="Shane Baz",
            game_time="19:07",
            game_date="2025-07-21",
            away_team_nerd_score=5.8,
            home_team_nerd_score=6.4,
            average_team_nerd_score=6.1,
            away_pitcher_nerd_score=7.2,
            home_pitcher_nerd_score=6.9,
            average_pitcher_nerd_score=7.05,
            gnerd_score=13.15,
            away_team_nerd_stats=team_nerd_details["TST"],
            home_team_nerd_stats=team_nerd_details["TST"],
            away_pitcher_nerd_stats=pitcher_nerd_details["Test Pitcher"],
            home_pitcher_nerd_stats=pitcher_nerd_details["Test Pitcher"],
            game_description="This is a test game with OpenAI description.",
            game_description_sources=[
                {"url": "https://example.com/article1", "title": "Game Preview"},
            ],
            game_description_provider="openai",
        )

        result = generate_game_detail_section(game_score, include_descriptions=True)

        # Check that OpenAI attribution is used with sources
        expected_attribution = "(A model from [OpenAI](https://www.openai.com) generated this text using instructions, the NERD scores, and these sources: [1](https://example.com/article1).)"
        assert expected_attribution in result

        # Verify old Claude attribution is not present
        assert "Claude](https://www.anthropic.com/claude)" not in result

    def test_generate_game_detail_section_with_unknown_provider(self) -> None:
        """Test game detail section falls back to Claude attribution for unknown provider."""
        team_nerd_details, pitcher_nerd_details = self.create_minimal_stats()

        game_score = GameScore(
            away_team="Chicago Cubs",
            home_team="Milwaukee Brewers",
            away_starter="Shota Imanaga",
            home_starter="Freddy Peralta",
            game_time="20:10",
            game_date="2025-07-22",
            away_team_nerd_score=5.5,
            home_team_nerd_score=6.8,
            average_team_nerd_score=6.15,
            away_pitcher_nerd_score=7.0,
            home_pitcher_nerd_score=7.3,
            average_pitcher_nerd_score=7.15,
            gnerd_score=13.3,
            away_team_nerd_stats=team_nerd_details["TST"],
            home_team_nerd_stats=team_nerd_details["TST"],
            away_pitcher_nerd_stats=pitcher_nerd_details["Test Pitcher"],
            home_pitcher_nerd_stats=pitcher_nerd_details["Test Pitcher"],
            game_description="This is a test game with unknown provider.",
            game_description_sources=[],
            game_description_provider="unknown_provider",  # Unknown provider
        )

        result = generate_game_detail_section(game_score, include_descriptions=True)

        # Check that it falls back to fallback attribution for unknown providers
        expected_attribution = "(An unable to be specified model (despite best intentions) generated this text using instructions and the NERD scores.)"
        assert expected_attribution in result

    def test_generate_game_detail_section_with_no_provider(self) -> None:
        """Test game detail section falls back to fallback attribution when provider is None."""
        team_nerd_details, pitcher_nerd_details = self.create_minimal_stats()

        game_score = GameScore(
            away_team="Atlanta Braves",
            home_team="Philadelphia Phillies",
            away_starter="Spencer Strider",
            home_starter="Zack Wheeler",
            game_time="19:05",
            game_date="2025-07-23",
            away_team_nerd_score=6.9,
            home_team_nerd_score=7.2,
            average_team_nerd_score=7.05,
            away_pitcher_nerd_score=8.8,
            home_pitcher_nerd_score=8.1,
            average_pitcher_nerd_score=8.45,
            gnerd_score=15.5,
            away_team_nerd_stats=team_nerd_details["TST"],
            home_team_nerd_stats=team_nerd_details["TST"],
            away_pitcher_nerd_stats=pitcher_nerd_details["Test Pitcher"],
            home_pitcher_nerd_stats=pitcher_nerd_details["Test Pitcher"],
            game_description="This is a test game with no provider info.",
            game_description_sources=[],
            game_description_provider=None,  # No provider specified
        )

        result = generate_game_detail_section(game_score, include_descriptions=True)

        # Check that it falls back to fallback attribution when no provider is specified
        expected_attribution = "(An unable to be specified model (despite best intentions) generated this text using instructions and the NERD scores.)"
        assert expected_attribution in result
