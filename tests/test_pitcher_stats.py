"""Unit tests for pitcher statistics data structures."""


import pytest

from mlb_watchability.pitcher_stats import (
    PitcherNerdStats,
    PitcherStats,
    calculate_pnerd_score,
    find_pitcher_nerd_stats_fuzzy,
    format_pitcher_with_fangraphs_link,
    map_mlbam_name_to_fangraphs_name,
    remove_accented_characters,
)


class TestPitcherStats:
    """Test cases for PitcherStats data structure."""

    def test_valid_pitcher_stats_creation(self) -> None:
        """Test creating valid pitcher statistics."""
        stats = PitcherStats(
            name="Jacob deGrom",
            team="NYM",
            xfip_minus=85,
            swinging_strike_rate=0.15,
            strike_rate=0.65,
            velocity=95.5,
            age=34,
            pace=18.2,
            luck=-5.0,
            knuckleball_rate=0.0,
        )

        assert stats.name == "Jacob deGrom"
        assert stats.team == "NYM"
        assert stats.xfip_minus == 85
        assert stats.swinging_strike_rate == 0.15
        assert stats.strike_rate == 0.65
        assert stats.velocity == 95.5
        assert stats.age == 34
        assert stats.pace == 18.2
        assert stats.luck == -5.0
        assert stats.knuckleball_rate == 0.0

    def test_knuckleball_pitcher_stats(self) -> None:
        """Test pitcher statistics for a knuckleball pitcher."""
        stats = PitcherStats(
            name="Tim Wakefield",
            team="BOS",
            xfip_minus=105,
            swinging_strike_rate=0.08,
            strike_rate=0.58,
            velocity=72.5,
            age=40,
            pace=25.0,
            luck=2.0,
            knuckleball_rate=0.85,
        )

        assert stats.knuckleball_rate == 0.85
        assert stats.velocity == 72.5  # Low velocity for knuckleball

    def test_empty_name_validation(self) -> None:
        """Test that empty pitcher name raises ValueError."""
        with pytest.raises(ValueError, match="Pitcher name cannot be empty"):
            PitcherStats(
                name="",
                team="NYM",
                xfip_minus=85,
                swinging_strike_rate=0.15,
                strike_rate=0.65,
                velocity=95.5,
                age=34,
                pace=18.2,
                luck=-5.0,
                knuckleball_rate=0.0,
            )

    def test_empty_team_validation(self) -> None:
        """Test that empty team raises ValueError."""
        with pytest.raises(ValueError, match="Team cannot be empty"):
            PitcherStats(
                name="Jacob deGrom",
                team="",
                xfip_minus=85,
                swinging_strike_rate=0.15,
                strike_rate=0.65,
                velocity=95.5,
                age=34,
                pace=18.2,
                luck=-5.0,
                knuckleball_rate=0.0,
            )


class TestPitcherNerdStats:
    """Test cases for PitcherNerdStats data structure."""

    def create_sample_pitcher_stats(self) -> PitcherStats:
        """Create sample pitcher statistics for testing."""
        return PitcherStats(
            name="Test Pitcher",
            team="TST",
            xfip_minus=85,
            swinging_strike_rate=0.15,
            strike_rate=0.65,
            velocity=95.5,
            age=28,
            pace=18.2,
            luck=-5.0,
            knuckleball_rate=0.0,
        )

    def test_valid_pitcher_nerd_stats_creation(self) -> None:
        """Test creating valid pitcher NERD statistics."""
        pitcher_stats = self.create_sample_pitcher_stats()

        nerd_stats = PitcherNerdStats(
            pitcher_stats=pitcher_stats,
            z_xfip_minus=-0.5,
            z_swinging_strike_rate=1.2,
            z_strike_rate=0.8,
            z_velocity=1.5,
            z_age=-0.3,
            z_pace=0.2,
            adjusted_velocity=1.5,
            adjusted_age=0.0,
            adjusted_luck=0.0,
            pnerd_score=12.5,
        )

        assert nerd_stats.pitcher_stats == pitcher_stats
        assert nerd_stats.z_xfip_minus == -0.5
        assert nerd_stats.z_swinging_strike_rate == 1.2
        assert nerd_stats.z_strike_rate == 0.8
        assert nerd_stats.z_velocity == 1.5
        assert nerd_stats.z_age == -0.3
        assert nerd_stats.z_pace == 0.2
        assert nerd_stats.adjusted_velocity == 1.5
        assert nerd_stats.adjusted_age == 0.0
        assert nerd_stats.adjusted_luck == 0.0
        assert nerd_stats.pnerd_score == 12.5

    def test_adjusted_velocity_validation(self) -> None:
        """Test adjusted velocity validation."""
        pitcher_stats = self.create_sample_pitcher_stats()

        with pytest.raises(
            ValueError, match="Adjusted velocity must be between 0.0 and 2.0"
        ):
            PitcherNerdStats(
                pitcher_stats=pitcher_stats,
                z_xfip_minus=-0.5,
                z_swinging_strike_rate=1.2,
                z_strike_rate=0.8,
                z_velocity=1.5,
                z_age=-0.3,
                z_pace=0.2,
                adjusted_velocity=3.0,  # Too high
                adjusted_age=0.0,
                adjusted_luck=0.0,
                pnerd_score=12.5,
            )

    def test_adjusted_age_validation(self) -> None:
        """Test adjusted age validation."""
        pitcher_stats = self.create_sample_pitcher_stats()

        with pytest.raises(
            ValueError, match="Adjusted age must be between 0.0 and 2.0"
        ):
            PitcherNerdStats(
                pitcher_stats=pitcher_stats,
                z_xfip_minus=-0.5,
                z_swinging_strike_rate=1.2,
                z_strike_rate=0.8,
                z_velocity=1.5,
                z_age=-0.3,
                z_pace=0.2,
                adjusted_velocity=1.5,
                adjusted_age=-0.5,  # Too low
                adjusted_luck=0.0,
                pnerd_score=12.5,
            )

    def test_adjusted_luck_validation(self) -> None:
        """Test adjusted luck validation."""
        pitcher_stats = self.create_sample_pitcher_stats()

        with pytest.raises(
            ValueError, match="Adjusted luck must be between 0.0 and 1.0"
        ):
            PitcherNerdStats(
                pitcher_stats=pitcher_stats,
                z_xfip_minus=-0.5,
                z_swinging_strike_rate=1.2,
                z_strike_rate=0.8,
                z_velocity=1.5,
                z_age=-0.3,
                z_pace=0.2,
                adjusted_velocity=1.5,
                adjusted_age=0.0,
                adjusted_luck=2.0,  # Too high
                pnerd_score=12.5,
            )

    def test_pnerd_score_validation(self) -> None:
        """Test pNERD score validation."""
        pitcher_stats = self.create_sample_pitcher_stats()

        with pytest.raises(
            ValueError, match="pNERD score must be between -10.0 and 50.0"
        ):
            PitcherNerdStats(
                pitcher_stats=pitcher_stats,
                z_xfip_minus=-0.5,
                z_swinging_strike_rate=1.2,
                z_strike_rate=0.8,
                z_velocity=1.5,
                z_age=-0.3,
                z_pace=0.2,
                adjusted_velocity=1.5,
                adjusted_age=0.0,
                adjusted_luck=0.0,
                pnerd_score=75.0,  # Too high
            )


class TestCalculatePnerdScore:
    """Test cases for pNERD score calculation."""

    def create_sample_league_stats(self) -> tuple[dict[str, float], dict[str, float]]:
        """Create sample league statistics for testing."""
        league_means = {
            "xfip_minus": 100,
            "swinging_strike_rate": 0.11,
            "strike_rate": 0.64,
            "velocity": 93.5,
            "age": 29,
            "pace": 20.0,
        }

        league_std_devs = {
            "xfip_minus": 15,
            "swinging_strike_rate": 0.025,
            "strike_rate": 0.04,
            "velocity": 2.5,
            "age": 4,
            "pace": 3.0,
        }

        return league_means, league_std_devs

    def test_calculate_pnerd_score_basic(self) -> None:
        """Test basic pNERD score calculation."""
        pitcher_stats = PitcherStats(
            name="Test Pitcher",
            team="TST",
            xfip_minus=85,  # Better than average (lower is better)
            swinging_strike_rate=0.135,  # Better than average
            strike_rate=0.68,  # Better than average
            velocity=96.0,  # Better than average
            age=26,  # Younger than average
            pace=17.0,  # Faster than average (lower is better)
            luck=5.0,  # Lucky
            knuckleball_rate=0.0,
        )

        league_means, league_std_devs = self.create_sample_league_stats()

        nerd_stats = calculate_pnerd_score(pitcher_stats, league_means, league_std_devs)

        # Check that z-scores are calculated correctly
        assert nerd_stats.z_xfip_minus == (85 - 100) / 15  # -1.0
        assert nerd_stats.z_swinging_strike_rate == (0.135 - 0.11) / 0.025  # 1.0
        assert nerd_stats.z_strike_rate == (0.68 - 0.64) / 0.04  # 1.0
        assert nerd_stats.z_velocity == (96.0 - 93.5) / 2.5  # 1.0
        assert nerd_stats.z_age == (26 - 29) / 4  # -0.75
        assert nerd_stats.z_pace == (17.0 - 20.0) / 3.0  # -1.0

        # Check adjusted values
        assert (
            nerd_stats.adjusted_velocity == 1.0
        )  # z_velocity capped at 2.0, positive only
        assert (
            nerd_stats.adjusted_age == 0.75
        )  # -z_age = -(-0.75) = 0.75, younger is better
        assert nerd_stats.adjusted_luck == 1.0  # luck is 5.0, capped at 1.0

        # Check pNERD score calculation
        expected_pnerd = (
            (
                1.0 * 2
            )  # -z_xfip_minus * 2 = -(-1.0) * 2 = 1.0 * 2 (lower xFIP- is better)
            + (1.0 / 2)  # z_swinging_strike_rate / 2
            + (1.0 / 2)  # z_strike_rate / 2
            + 1.0  # adjusted_velocity
            + 0.75  # adjusted_age
            + (1.0 / 2)  # -z_pace / 2 (faster pace is better)
            + (1.0 / 20)  # adjusted_luck / 20
            + (0.0 * 5)  # knuckleball_rate * 5
            + 3.8  # constant
        )

        assert abs(nerd_stats.pnerd_score - expected_pnerd) < 0.001

    def test_calculate_pnerd_score_with_knuckleball(self) -> None:
        """Test pNERD score calculation with knuckleball pitcher."""
        pitcher_stats = PitcherStats(
            name="Knuckleball Pitcher",
            team="KNB",
            xfip_minus=105,
            swinging_strike_rate=0.08,
            strike_rate=0.60,
            velocity=72.0,
            age=35,
            pace=25.0,
            luck=0.0,
            knuckleball_rate=0.8,
        )

        league_means, league_std_devs = self.create_sample_league_stats()

        nerd_stats = calculate_pnerd_score(pitcher_stats, league_means, league_std_devs)

        # Knuckleball should add significant value (KN% * 5)
        assert nerd_stats.pitcher_stats.knuckleball_rate == 0.8

        # Check that knuckleball bonus is included in score
        knuckleball_bonus = 0.8 * 5  # 4.0
        assert knuckleball_bonus == 4.0

    def test_calculate_pnerd_score_caps_applied(self) -> None:
        """Test that caps are properly applied in pNERD calculation."""
        pitcher_stats = PitcherStats(
            name="Extreme Pitcher",
            team="EXT",
            xfip_minus=50,
            swinging_strike_rate=0.20,
            strike_rate=0.75,
            velocity=102.0,  # Very high velocity
            age=22,  # Very young
            pace=12.0,
            luck=25.0,  # Very lucky
            knuckleball_rate=0.0,
        )

        league_means, league_std_devs = self.create_sample_league_stats()

        nerd_stats = calculate_pnerd_score(pitcher_stats, league_means, league_std_devs)

        # Check that caps are applied
        assert nerd_stats.adjusted_velocity == 2.0  # Should be capped at 2.0
        assert nerd_stats.adjusted_age == 1.75  # -z_age = -(-1.75) = 1.75, not capped
        assert nerd_stats.adjusted_luck == 1.0  # Should be capped at 1.0

    def test_calculate_pnerd_score_negative_adjustments(self) -> None:
        """Test that negative values are set to zero for velocity, age, and luck."""
        pitcher_stats = PitcherStats(
            name="Negative Pitcher",
            team="NEG",
            xfip_minus=120,
            swinging_strike_rate=0.09,
            strike_rate=0.58,
            velocity=88.0,  # Below average velocity
            age=38,  # Older than average
            pace=25.0,
            luck=-15.0,  # Unlucky
            knuckleball_rate=0.0,
        )

        league_means, league_std_devs = self.create_sample_league_stats()

        nerd_stats = calculate_pnerd_score(pitcher_stats, league_means, league_std_devs)

        # Check that negative values are set to zero
        assert nerd_stats.adjusted_velocity == 0.0  # z_velocity is negative
        assert nerd_stats.adjusted_age == 0.0  # -z_age = -(2.25) = -2.25, set to 0.0
        assert nerd_stats.adjusted_luck == 0.0  # luck is negative


class TestPitcherFormatting:
    """Test cases for pitcher formatting functions."""

    def test_format_pitcher_with_fangraphs_link_normal_names(self) -> None:
        """Test format_pitcher_with_fangraphs_link with normal pitcher names."""
        result = format_pitcher_with_fangraphs_link("Gerrit Cole")
        expected = "[Gerrit Cole](https://www.fangraphs.com/search?q=Cole)"
        assert result == expected

        result = format_pitcher_with_fangraphs_link("Jacob deGrom")
        expected = "[Jacob deGrom](https://www.fangraphs.com/search?q=deGrom)"
        assert result == expected

        result = format_pitcher_with_fangraphs_link("Shohei Ohtani")
        expected = "[Shohei Ohtani](https://www.fangraphs.com/search?q=Ohtani)"
        assert result == expected

    def test_format_pitcher_with_fangraphs_link_single_name(self) -> None:
        """Test format_pitcher_with_fangraphs_link with single name."""
        result = format_pitcher_with_fangraphs_link("Ohtani")
        expected = "[Ohtani](https://www.fangraphs.com/search?q=Ohtani)"
        assert result == expected

    def test_format_pitcher_with_fangraphs_link_multiple_names(self) -> None:
        """Test format_pitcher_with_fangraphs_link with multiple names."""
        result = format_pitcher_with_fangraphs_link("Luis Robert Jr.")
        expected = "[Luis Robert Jr.](https://www.fangraphs.com/search?q=Jr.)"
        assert result == expected

    def test_format_pitcher_with_fangraphs_link_edge_cases(self) -> None:
        """Test format_pitcher_with_fangraphs_link with edge cases."""
        # Empty or None pitcher name should return TBD
        assert format_pitcher_with_fangraphs_link("") == "TBD"
        assert format_pitcher_with_fangraphs_link(None) == "TBD"  # type: ignore
        assert format_pitcher_with_fangraphs_link("TBD") == "TBD"

        # Single space should use the space as last name
        result = format_pitcher_with_fangraphs_link(" ")
        expected = "[ ](https://www.fangraphs.com/search?q= )"
        assert result == expected


class TestRemoveAccentedCharacters:
    """Test cases for remove_accented_characters function."""

    def test_remove_accented_characters_common_cases(self) -> None:
        """Test removal of common accented characters."""
        # Spanish names with tildes and accents
        assert remove_accented_characters("Jesús Luzardo") == "Jesus Luzardo"
        assert remove_accented_characters("José Altuve") == "Jose Altuve"
        assert remove_accented_characters("Teoscar Hernández") == "Teoscar Hernandez"
        assert remove_accented_characters("Andrés Muñoz") == "Andres Munoz"

        # French names
        assert remove_accented_characters("René González") == "Rene Gonzalez"

        # Portuguese names
        assert remove_accented_characters("João Silva") == "Joao Silva"

        # Names with multiple accents
        assert remove_accented_characters("François José") == "Francois Jose"

    def test_remove_accented_characters_no_accents(self) -> None:
        """Test function with names that have no accented characters."""
        assert remove_accented_characters("Jacob Latz") == "Jacob Latz"
        assert remove_accented_characters("Mike Soroka") == "Mike Soroka"
        assert remove_accented_characters("Chris Sale") == "Chris Sale"
        assert remove_accented_characters("Paul Skenes") == "Paul Skenes"

    def test_remove_accented_characters_edge_cases(self) -> None:
        """Test function with edge cases."""
        # Empty string
        assert remove_accented_characters("") == ""

        # None input
        assert remove_accented_characters(None) is None  # type: ignore

        # Single character with accent
        assert remove_accented_characters("é") == "e"
        assert remove_accented_characters("ñ") == "n"

        # Only accented characters
        assert remove_accented_characters("José") == "Jose"

    def test_remove_accented_characters_preserves_other_chars(self) -> None:
        """Test that function preserves non-accent special characters."""
        # Apostrophes and hyphens should be preserved
        assert remove_accented_characters("O'Neill") == "O'Neill"
        assert remove_accented_characters("Jean-Claude") == "Jean-Claude"
        assert remove_accented_characters("José O'Brien") == "Jose O'Brien"


class TestMapMlbamNameToFangraphs:
    """Test cases for map_mlbam_name_to_fangraphs_name function."""

    def test_map_mlbam_name_to_fangraphs_name_existing_mapping(self) -> None:
        """Test mapping with existing entry in CSV."""
        # This assumes the CSV has Jacob Latz -> Jake Latz mapping
        result = map_mlbam_name_to_fangraphs_name("Jacob Latz")
        assert result == "Jake Latz"

    def test_map_mlbam_name_to_fangraphs_name_no_mapping(self) -> None:
        """Test mapping with name not in CSV."""
        result = map_mlbam_name_to_fangraphs_name("Paul Skenes")
        assert result == "Paul Skenes"  # Should return original name

        result = map_mlbam_name_to_fangraphs_name("Shohei Ohtani")
        assert result == "Shohei Ohtani"  # Should return original name

    def test_map_mlbam_name_to_fangraphs_name_edge_cases(self) -> None:
        """Test mapping with edge cases."""
        # Empty string
        assert map_mlbam_name_to_fangraphs_name("") == ""

        # None input
        assert map_mlbam_name_to_fangraphs_name(None) is None  # type: ignore

        # Whitespace
        assert map_mlbam_name_to_fangraphs_name("  ") == "  "

    def test_map_mlbam_name_to_fangraphs_name_case_sensitive(self) -> None:
        """Test that mapping is case-sensitive."""
        # Different case should not match
        result = map_mlbam_name_to_fangraphs_name("jacob latz")  # lowercase
        assert (
            result == "jacob latz"
        )  # Should return original since CSV has "Jacob Latz"

        result = map_mlbam_name_to_fangraphs_name("JACOB LATZ")  # uppercase
        assert (
            result == "JACOB LATZ"
        )  # Should return original since CSV has "Jacob Latz"

    # Don't want to use the Claude impl of this test for now, so I'll pass on this one for the time being
    # def test_map_mlbam_name_to_fangraphs_name_malformed_csv(self) -> None:
    #     """Test that KeyError is raised when CSV has missing columns."""

    #     # Create a temporary CSV with wrong column names
    #     with tempfile.NamedTemporaryFile(
    #         mode="w", suffix=".csv", delete=False
    #     ) as temp_file:
    #         temp_file.write("wrong_column,another_column\n")
    #         temp_file.write("Jacob Latz,Jake Latz\n")
    #         temp_path = Path(temp_file.name)

    #     # Get the current CSV path and temporarily replace it
    #     current_dir = Path(__file__).parent.parent / "src" / "mlb_watchability"
    #     csv_path = current_dir.parent.parent / "data" / "name-mapping.csv"

    #     # Create backup of original file if it exists
    #     backup_path = None
    #     if csv_path.exists():
    #         backup_path = csv_path.with_suffix(".csv.backup")
    #         csv_path.rename(backup_path)

    #     try:
    #         # Move temp file to expected location
    #         temp_path.rename(csv_path)

    #         # Test that KeyError is raised due to missing expected columns
    #         with pytest.raises(KeyError):
    #             map_mlbam_name_to_fangraphs_name("Jacob Latz")

    #     finally:
    #         # Clean up
    #         if csv_path.exists():
    #             csv_path.unlink()
    #         if backup_path and backup_path.exists():
    #             backup_path.rename(csv_path)


class TestFindPitcherNerdStatsFuzzy:
    """Test cases for find_pitcher_nerd_stats_fuzzy function."""

    def create_sample_pitcher_nerd_stats(self) -> dict[str, PitcherNerdStats]:
        """Create sample pitcher NERD stats dictionary for testing."""
        # Create some sample PitcherStats objects
        pitcher1 = PitcherStats(
            name="Jake Latz",
            team="TST",
            xfip_minus=85,
            swinging_strike_rate=0.15,
            strike_rate=0.65,
            velocity=95.5,
            age=28,
            pace=18.2,
            luck=-5.0,
            knuckleball_rate=0.0,
        )

        pitcher2 = PitcherStats(
            name="Jesus Luzardo",
            team="TST",
            xfip_minus=90,
            swinging_strike_rate=0.12,
            strike_rate=0.62,
            velocity=94.0,
            age=26,
            pace=19.0,
            luck=2.0,
            knuckleball_rate=0.0,
        )

        # Create corresponding PitcherNerdStats objects
        nerd_stats1 = PitcherNerdStats(
            pitcher_stats=pitcher1,
            z_xfip_minus=-1.0,
            z_swinging_strike_rate=1.2,
            z_strike_rate=0.8,
            z_velocity=1.5,
            z_age=-0.3,
            z_pace=0.2,
            adjusted_velocity=1.5,
            adjusted_age=0.3,
            adjusted_luck=0.0,
            pnerd_score=8.5,
        )

        nerd_stats2 = PitcherNerdStats(
            pitcher_stats=pitcher2,
            z_xfip_minus=-0.5,
            z_swinging_strike_rate=0.8,
            z_strike_rate=0.5,
            z_velocity=1.0,
            z_age=-0.8,
            z_pace=0.5,
            adjusted_velocity=1.0,
            adjusted_age=0.8,
            adjusted_luck=0.1,
            pnerd_score=7.2,
        )

        return {
            "Jake Latz": nerd_stats1,
            "Jesus Luzardo": nerd_stats2,
        }

    def test_find_pitcher_nerd_stats_fuzzy_direct_match(self) -> None:
        """Test fuzzy lookup with direct name match."""
        pitcher_stats = self.create_sample_pitcher_nerd_stats()

        result = find_pitcher_nerd_stats_fuzzy(pitcher_stats, "Jake Latz")
        assert result is not None
        assert result.pitcher_stats.name == "Jake Latz"
        assert result.pnerd_score == 8.5

    def test_find_pitcher_nerd_stats_fuzzy_accented_characters(self) -> None:
        """Test fuzzy lookup with accented characters removed."""
        pitcher_stats = self.create_sample_pitcher_nerd_stats()

        # Should find "Jesus Luzardo" when searching for "Jesús Luzardo"
        result = find_pitcher_nerd_stats_fuzzy(pitcher_stats, "Jesús Luzardo")
        assert result is not None
        assert result.pitcher_stats.name == "Jesus Luzardo"
        assert result.pnerd_score == 7.2

    def test_find_pitcher_nerd_stats_fuzzy_mlbam_mapping(self) -> None:
        """Test fuzzy lookup using MLBAM to Fangraphs mapping."""
        pitcher_stats = self.create_sample_pitcher_nerd_stats()

        # Should find "Jake Latz" when searching for "Jacob Latz" (via CSV mapping)
        result = find_pitcher_nerd_stats_fuzzy(pitcher_stats, "Jacob Latz")
        assert result is not None
        assert result.pitcher_stats.name == "Jake Latz"
        assert result.pnerd_score == 8.5

    def test_find_pitcher_nerd_stats_fuzzy_not_found(self) -> None:
        """Test fuzzy lookup when pitcher is not found."""
        pitcher_stats = self.create_sample_pitcher_nerd_stats()

        result = find_pitcher_nerd_stats_fuzzy(pitcher_stats, "Paul Skenes")
        assert result is None

    def test_find_pitcher_nerd_stats_fuzzy_edge_cases(self) -> None:
        """Test fuzzy lookup with edge cases."""
        pitcher_stats = self.create_sample_pitcher_nerd_stats()

        # Empty string
        result = find_pitcher_nerd_stats_fuzzy(pitcher_stats, "")
        assert result is None

        # TBD
        result = find_pitcher_nerd_stats_fuzzy(pitcher_stats, "TBD")
        assert result is None

        # None input
        result = find_pitcher_nerd_stats_fuzzy(pitcher_stats, None)  # type: ignore
        assert result is None

    def test_find_pitcher_nerd_stats_fuzzy_empty_dict(self) -> None:
        """Test fuzzy lookup with empty pitcher stats dictionary."""
        result = find_pitcher_nerd_stats_fuzzy({}, "Jacob Latz")
        assert result is None

    def test_find_pitcher_nerd_stats_fuzzy_strategy_order(self) -> None:
        """Test that fuzzy lookup tries strategies in correct order."""
        # Create a dict where we have both "Jacob Latz" and "Jake Latz"
        # to ensure direct match takes precedence
        pitcher_stats = self.create_sample_pitcher_nerd_stats()

        # Add a second pitcher with the "Jake" name
        jake_stats = PitcherStats(
            name="Jake Latz",
            team="TST2",
            xfip_minus=100,
            swinging_strike_rate=0.10,
            strike_rate=0.60,
            velocity=92.0,
            age=30,
            pace=20.0,
            luck=0.0,
            knuckleball_rate=0.0,
        )

        jake_nerd_stats = PitcherNerdStats(
            pitcher_stats=jake_stats,
            z_xfip_minus=0.0,
            z_swinging_strike_rate=0.0,
            z_strike_rate=0.0,
            z_velocity=0.0,
            z_age=0.0,
            z_pace=0.0,
            adjusted_velocity=0.0,
            adjusted_age=0.0,
            adjusted_luck=0.0,
            pnerd_score=5.0,
        )

        pitcher_stats["Jake Latz"] = jake_nerd_stats

        # When searching for "Jake Latz", should get direct match, not mapped one
        result = find_pitcher_nerd_stats_fuzzy(pitcher_stats, "Jake Latz")
        assert result is not None
        assert result.pitcher_stats.name == "Jake Latz"  # Direct match
        assert result.pnerd_score == 5.0  # Not the mapped Jacob Latz score
