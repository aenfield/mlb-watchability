"""Tests for team mappings module."""

from mlb_watchability.team_mappings import (
    PAYROLL_TO_STANDARD_ABBREVIATION,
    TEAM_NAME_TO_ABBREVIATION,
    get_team_abbreviation,
    normalize_payroll_team_abbreviation,
)


class TestTeamMappings:
    """Test cases for team mapping functions."""

    def test_get_team_abbreviation_known_teams(self) -> None:
        """Test get_team_abbreviation with known team names."""
        assert get_team_abbreviation("Arizona Diamondbacks") == "ARI"
        assert get_team_abbreviation("Boston Red Sox") == "BOS"
        assert get_team_abbreviation("New York Yankees") == "NYY"
        assert get_team_abbreviation("Los Angeles Dodgers") == "LAD"
        assert get_team_abbreviation("San Francisco Giants") == "SFG"

    def test_get_team_abbreviation_unknown_team(self) -> None:
        """Test get_team_abbreviation with unknown team name."""
        assert get_team_abbreviation("Unknown Team") == "Unknown Team"
        assert get_team_abbreviation("") == ""

    def test_normalize_payroll_team_abbreviation_known_mappings(self) -> None:
        """Test normalize_payroll_team_abbreviation with known mappings."""
        assert normalize_payroll_team_abbreviation("TB") == "TBR"
        assert normalize_payroll_team_abbreviation("WSH") == "WSN"
        assert normalize_payroll_team_abbreviation("SD") == "SDP"
        assert normalize_payroll_team_abbreviation("SF") == "SFG"
        assert normalize_payroll_team_abbreviation("KC") == "KCR"

    def test_normalize_payroll_team_abbreviation_no_mapping(self) -> None:
        """Test normalize_payroll_team_abbreviation with no mapping needed."""
        assert normalize_payroll_team_abbreviation("BOS") == "BOS"
        assert normalize_payroll_team_abbreviation("NYY") == "NYY"
        assert normalize_payroll_team_abbreviation("LAD") == "LAD"
        assert normalize_payroll_team_abbreviation("Unknown") == "Unknown"

    def test_team_name_to_abbreviation_completeness(self) -> None:
        """Test that all 30 MLB teams are in the mapping."""
        # Should have exactly 30 teams
        assert len(TEAM_NAME_TO_ABBREVIATION) == 30

        # Check a few key teams to ensure mapping is correct
        expected_teams = {
            "Arizona Diamondbacks": "ARI",
            "Atlanta Braves": "ATL",
            "Baltimore Orioles": "BAL",
            "Boston Red Sox": "BOS",
            "Chicago Cubs": "CHC",
            "Chicago White Sox": "CWS",
            "Cincinnati Reds": "CIN",
            "Cleveland Guardians": "CLE",
            "Colorado Rockies": "COL",
            "Detroit Tigers": "DET",
            "Houston Astros": "HOU",
            "Kansas City Royals": "KCR",
            "Los Angeles Angels": "LAA",
            "Los Angeles Dodgers": "LAD",
            "Miami Marlins": "MIA",
            "Milwaukee Brewers": "MIL",
            "Minnesota Twins": "MIN",
            "New York Mets": "NYM",
            "New York Yankees": "NYY",
            "Oakland Athletics": "OAK",
            "Philadelphia Phillies": "PHI",
            "Pittsburgh Pirates": "PIT",
            "San Diego Padres": "SDP",
            "San Francisco Giants": "SFG",
            "Seattle Mariners": "SEA",
            "St. Louis Cardinals": "STL",
            "Tampa Bay Rays": "TBR",
            "Texas Rangers": "TEX",
            "Toronto Blue Jays": "TOR",
            "Washington Nationals": "WSN",
        }

        for team_name, expected_abbr in expected_teams.items():
            assert TEAM_NAME_TO_ABBREVIATION[team_name] == expected_abbr

    def test_payroll_mapping_completeness(self) -> None:
        """Test that payroll mapping contains expected mappings."""
        expected_mappings = {
            "TB": "TBR",
            "WSH": "WSN",
            "SD": "SDP",
            "SF": "SFG",
            "KC": "KCR",
        }

        assert len(PAYROLL_TO_STANDARD_ABBREVIATION) == len(expected_mappings)

        for payroll_abbr, expected_standard in expected_mappings.items():
            assert PAYROLL_TO_STANDARD_ABBREVIATION[payroll_abbr] == expected_standard

    def test_no_conflicts_between_mappings(self) -> None:
        """Test that there are no conflicts between standard and payroll abbreviations."""
        # All values in TEAM_NAME_TO_ABBREVIATION should be standard abbreviations
        standard_abbreviations = set(TEAM_NAME_TO_ABBREVIATION.values())

        # All values in PAYROLL_TO_STANDARD_ABBREVIATION should also be standard abbreviations
        payroll_mapped_abbreviations = set(PAYROLL_TO_STANDARD_ABBREVIATION.values())

        # All payroll mapped abbreviations should exist in standard abbreviations
        assert payroll_mapped_abbreviations.issubset(standard_abbreviations)

        # None of the payroll keys should conflict with standard abbreviations
        payroll_keys = set(PAYROLL_TO_STANDARD_ABBREVIATION.keys())
        conflicts = payroll_keys.intersection(standard_abbreviations)

        # The only acceptable conflict is if a payroll key maps to itself
        # (which shouldn't happen in our current setup, but this test allows for it)
        for conflict in conflicts:
            if conflict in PAYROLL_TO_STANDARD_ABBREVIATION:
                assert PAYROLL_TO_STANDARD_ABBREVIATION[conflict] == conflict
