"""Unit tests for team statistics data structures."""

import pytest

from mlb_watchability.team_stats import (
    TeamNerdStats,
    TeamStats,
)


class TestTeamStats:
    """Test cases for TeamStats data structure."""

    def test_valid_team_stats_creation(self) -> None:
        """Test creating valid team statistics."""
        stats = TeamStats(
            name="Los Angeles Dodgers",
            batting_runs=45.2,
            barrel_rate=0.089,
            baserunning_runs=8.5,
            fielding_runs=12.3,
            payroll=285.6,
            age=28.5,
            luck=3.2,
        )

        assert stats.name == "Los Angeles Dodgers"
        assert stats.batting_runs == 45.2
        assert stats.barrel_rate == 0.089
        assert stats.baserunning_runs == 8.5
        assert stats.fielding_runs == 12.3
        assert stats.payroll == 285.6
        assert stats.age == 28.5
        assert stats.luck == 3.2

    def test_low_payroll_team_stats(self) -> None:
        """Test team statistics for a low payroll team."""
        stats = TeamStats(
            name="Pittsburgh Pirates",
            batting_runs=-35.8,
            barrel_rate=0.028,
            baserunning_runs=-12.1,
            fielding_runs=-8.7,
            payroll=65.2,
            age=26.8,
            luck=-5.5,
        )

        assert stats.payroll == 65.2  # Low payroll
        assert stats.batting_runs == -35.8  # Below average batting
        assert stats.luck == -5.5  # Unlucky

    def test_empty_name_validation(self) -> None:
        """Test that empty team name raises ValueError."""
        with pytest.raises(ValueError, match="Team name cannot be empty"):
            TeamStats(
                name="",
                batting_runs=45.2,
                barrel_rate=0.045,
                baserunning_runs=8.5,
                fielding_runs=12.3,
                payroll=285.6,
                age=28.5,
                luck=3.2,
            )


class TestTeamNerdStats:
    """Test cases for TeamNerdStats data structure."""

    def create_sample_team_stats(self) -> TeamStats:
        """Create sample team statistics for testing."""
        return TeamStats(
            name="Test Team",
            batting_runs=25.0,
            barrel_rate=0.040,
            baserunning_runs=5.0,
            fielding_runs=8.0,
            payroll=150.0,
            age=27.5,
            luck=2.0,
        )

    def test_valid_team_nerd_stats_creation(self) -> None:
        """Test creating valid team NERD statistics."""
        team_stats = self.create_sample_team_stats()

        nerd_stats = TeamNerdStats(
            team_stats=team_stats,
            z_batting_runs=0.8,
            z_barrel_rate=0.5,
            z_baserunning_runs=0.3,
            z_fielding_runs=0.6,
            z_luck=-0.2,
            z_payroll=0.4,
            z_age=-0.3,
            adjusted_payroll=0.0,
            adjusted_age=0.3,
            adjusted_luck=2.0,
            tnerd_score=8.5,
        )

        assert nerd_stats.team_stats == team_stats
        assert nerd_stats.z_batting_runs == 0.8
        assert nerd_stats.z_barrel_rate == 0.5
        assert nerd_stats.z_baserunning_runs == 0.3
        assert nerd_stats.z_fielding_runs == 0.6
        assert nerd_stats.z_luck == -0.2
        assert nerd_stats.z_payroll == 0.4
        assert nerd_stats.z_age == -0.3
        assert nerd_stats.adjusted_payroll == 0.0
        assert nerd_stats.adjusted_age == 0.3
        assert nerd_stats.adjusted_luck == 2.0
        assert nerd_stats.tnerd_score == 8.5


class TestTeamNerdStatsFromStatsAndMeans:
    """Test cases for TeamNerdStats.from_stats_and_means class method."""

    def create_sample_league_stats(self) -> tuple[dict[str, float], dict[str, float]]:
        """Create sample league statistics for testing."""
        league_means = {
            "batting_runs": 0.0,
            "barrel_rate": 0.035,
            "baserunning_runs": 0.0,
            "fielding_runs": 4.20,
            "luck": 0.0,
            "payroll": 140.0,
            "age": 28.5,
        }

        league_std_devs = {
            "batting_runs": 30.0,
            "barrel_rate": 0.008,
            "baserunning_runs": 15.0,
            "fielding_runs": 0.40,
            "luck": 20.0,
            "payroll": 50.0,
            "age": 1.5,
        }

        return league_means, league_std_devs

    def test_calculate_tnerd_score_basic(self) -> None:
        """Test basic tNERD score calculation."""
        team_stats = TeamStats(
            name="Test Team",
            batting_runs=30.0,  # Above average
            barrel_rate=0.043,  # Above average
            baserunning_runs=15.0,  # Above average
            fielding_runs=6.0,  # Above average but within valid z-score range
            payroll=90.0,  # Below average (better for tNERD)
            age=26.0,  # Younger than average (better)
            luck=4.0,  # Lucky
        )

        league_means, league_std_devs = self.create_sample_league_stats()

        nerd_stats = TeamNerdStats.from_stats_and_means(
            team_stats, league_means, league_std_devs
        )

        # Check that z-scores are calculated correctly
        assert nerd_stats.z_batting_runs == (30.0 - 0.0) / 30.0  # 1.0
        assert nerd_stats.z_barrel_rate == (0.043 - 0.035) / 0.008  # 1.0
        assert nerd_stats.z_baserunning_runs == (15.0 - 0.0) / 15.0  # 1.0
        assert nerd_stats.z_fielding_runs == (6.0 - 4.20) / 0.40  # 4.5
        assert nerd_stats.z_luck == (4.0 - 0.0) / 20.0  # 0.2
        assert nerd_stats.z_payroll == (90.0 - 140.0) / 50.0  # -1.0
        assert nerd_stats.z_age == (26.0 - 28.5) / 1.5  # -1.67 (approximately)

        # Check adjusted values
        assert (
            nerd_stats.adjusted_payroll == 1.0
        )  # -z_payroll = -(-1.0) = 1.0, below average is better
        assert (
            abs(nerd_stats.adjusted_age - 1.67) < 0.01
        )  # -z_age = -(-1.67) = 1.67, younger is better
        assert nerd_stats.adjusted_luck == 0.2  # luck is 0.2, not capped

        # Check tNERD score calculation
        expected_tnerd = (
            1.0  # z_batting_runs
            + 1.0  # z_barrel_rate
            + 1.0  # z_baserunning_runs
            + 4.5  # z_fielding_runs
            + 1.0  # adjusted_payroll
            + 1.67  # adjusted_age (approximately)
            + 0.2  # adjusted_luck
            + 4.0  # constant
        )

        assert abs(nerd_stats.tnerd_score - expected_tnerd) < 0.01

    def test_calculate_tnerd_score_negative_adjustments(self) -> None:
        """Test that negative values are set to zero for payroll, age, and luck."""
        team_stats = TeamStats(
            name="Negative Team",
            batting_runs=0.0,  # Average
            barrel_rate=0.035,  # Average
            baserunning_runs=0.0,  # Average
            fielding_runs=4.20,  # Average
            payroll=200.0,  # Above average (worse for tNERD)
            age=31.0,  # Older than average (worse)
            luck=-8.0,  # Unlucky
        )

        league_means, league_std_devs = self.create_sample_league_stats()

        nerd_stats = TeamNerdStats.from_stats_and_means(
            team_stats, league_means, league_std_devs
        )

        # Check that negative values are set to zero
        assert nerd_stats.adjusted_payroll == 0.0  # -z_payroll is negative
        assert nerd_stats.adjusted_age == 0.0  # -z_age is negative
        assert nerd_stats.adjusted_luck == 0.0  # luck is negative

    def test_calculate_tnerd_score_luck_cap(self) -> None:
        """Test that luck is properly capped at 2.0."""
        team_stats = TeamStats(
            name="Very Lucky Team",
            batting_runs=15.0,  # Above average to compensate for other factors
            barrel_rate=0.043,  # Above average
            baserunning_runs=8.0,  # Above average
            fielding_runs=6.0,  # Above average but within valid z-score range
            payroll=140.0,
            age=28.5,
            luck=50.0,  # Very lucky - should be capped at 2.0
        )

        league_means, league_std_devs = self.create_sample_league_stats()

        nerd_stats = TeamNerdStats.from_stats_and_means(
            team_stats, league_means, league_std_devs
        )

        # Check that luck is capped at 2.0
        # z_luck = (50.0 - 0.0) / 20.0 = 2.5, capped at 2.0
        assert nerd_stats.adjusted_luck == 2.0

    def test_calculate_tnerd_score_all_average(self) -> None:
        """Test tNERD score calculation with all average values."""
        team_stats = TeamStats(
            name="Average Team",
            batting_runs=0.0,  # League average
            barrel_rate=0.035,  # League average
            baserunning_runs=0.0,  # League average
            fielding_runs=4.20,  # League average
            payroll=140.0,  # League average
            age=28.5,  # League average
            luck=0.0,  # No luck
        )

        league_means, league_std_devs = self.create_sample_league_stats()

        nerd_stats = TeamNerdStats.from_stats_and_means(
            team_stats, league_means, league_std_devs
        )

        # All z-scores should be 0.0
        assert nerd_stats.z_batting_runs == 0.0
        assert nerd_stats.z_barrel_rate == 0.0
        assert nerd_stats.z_baserunning_runs == 0.0
        assert nerd_stats.z_fielding_runs == 0.0  # League average
        assert nerd_stats.z_luck == 0.0
        assert nerd_stats.z_payroll == 0.0
        assert nerd_stats.z_age == 0.0

        # All adjusted values should be 0.0
        assert nerd_stats.adjusted_payroll == 0.0
        assert nerd_stats.adjusted_age == 0.0
        assert nerd_stats.adjusted_luck == 0.0

        # tNERD score should be the constant only (all other values are 0.0)
        expected_tnerd = 4.0  # constant + all zeros
        assert abs(nerd_stats.tnerd_score - expected_tnerd) < 0.01


class TestTeamNerdStatsComponents:
    """Test the component properties of TeamNerdStats."""

    def test_team_nerd_stats_components(self) -> None:
        """Test that component properties return correct values."""
        team_stats = TeamStats(
            name="Test Team",
            batting_runs=10.0,
            barrel_rate=0.08,
            baserunning_runs=5.0,
            fielding_runs=8.0,
            payroll=150.0,
            age=27.0,
            luck=3.0,
        )

        league_means = {
            "batting_runs": 0.0,
            "barrel_rate": 0.06,
            "baserunning_runs": 0.0,
            "fielding_runs": 0.0,
            "payroll": 200.0,
            "age": 29.0,
            "luck": 0.0,
        }

        league_std_devs = {
            "batting_runs": 20.0,
            "barrel_rate": 0.02,
            "baserunning_runs": 10.0,
            "fielding_runs": 15.0,
            "payroll": 100.0,
            "age": 2.0,
            "luck": 5.0,
        }

        nerd_stats = TeamNerdStats.from_stats_and_means(
            team_stats, league_means, league_std_devs
        )

        # Test individual component properties
        # z_batting_runs = (10.0 - 0.0) / 20.0 = 0.5
        assert nerd_stats.batting_component == pytest.approx(0.5)

        # z_barrel_rate = (0.08 - 0.06) / 0.02 = 1.0
        assert nerd_stats.barrel_component == pytest.approx(1.0)

        # z_baserunning_runs = (5.0 - 0.0) / 10.0 = 0.5
        assert nerd_stats.baserunning_component == pytest.approx(0.5)

        # z_fielding_runs = (8.0 - 0.0) / 15.0 = 0.533
        assert nerd_stats.fielding_component == pytest.approx(0.533, abs=1e-3)

        # z_payroll = (150.0 - 200.0) / 100.0 = -0.5
        # adjusted_payroll = max(0.0, -(-0.5)) = 0.5
        assert nerd_stats.payroll_component == pytest.approx(0.5)

        # z_age = (27.0 - 29.0) / 2.0 = -1.0
        # adjusted_age = max(0.0, -(-1.0)) = 1.0
        assert nerd_stats.age_component == pytest.approx(1.0)

        # z_luck = (3.0 - 0.0) / 5.0 = 0.6
        # adjusted_luck = max(0.0, min(2.0, 0.6)) = 0.6
        assert nerd_stats.luck_component == pytest.approx(0.6)

        # constant = 4.0
        assert nerd_stats.constant_component == pytest.approx(4.0)

    def test_verify_tnerd_calculation(self) -> None:
        """Test that the sum of components equals the tNERD score."""
        team_stats = TeamStats(
            name="Test Team",
            batting_runs=10.0,
            barrel_rate=0.08,
            baserunning_runs=5.0,
            fielding_runs=8.0,
            payroll=150.0,
            age=27.0,
            luck=3.0,
        )

        league_means = {
            "batting_runs": 0.0,
            "barrel_rate": 0.06,
            "baserunning_runs": 0.0,
            "fielding_runs": 0.0,
            "payroll": 200.0,
            "age": 29.0,
            "luck": 0.0,
        }

        league_std_devs = {
            "batting_runs": 20.0,
            "barrel_rate": 0.02,
            "baserunning_runs": 10.0,
            "fielding_runs": 15.0,
            "payroll": 100.0,
            "age": 2.0,
            "luck": 5.0,
        }

        nerd_stats = TeamNerdStats.from_stats_and_means(
            team_stats, league_means, league_std_devs
        )

        # Verify that sum of components equals tNERD score
        calculated_total = (
            nerd_stats.batting_component
            + nerd_stats.barrel_component
            + nerd_stats.baserunning_component
            + nerd_stats.fielding_component
            + nerd_stats.payroll_component
            + nerd_stats.age_component
            + nerd_stats.luck_component
            + nerd_stats.constant_component
        )
        assert abs(calculated_total - nerd_stats.tnerd_score) < 0.001
