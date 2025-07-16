"""Unit tests for team statistics data structures."""

import pytest

from mlb_watchability.team_stats import (
    TeamNerdStats,
    TeamStats,
    calculate_tnerd_score,
)


class TestTeamStats:
    """Test cases for TeamStats data structure."""

    def test_valid_team_stats_creation(self) -> None:
        """Test creating valid team statistics."""
        stats = TeamStats(
            name="Los Angeles Dodgers",
            batting_runs=45.2,
            home_run_rate=0.045,
            baserunning_runs=8.5,
            bullpen_xfip=3.85,
            defensive_runs=12.3,
            payroll=285.6,
            age=28.5,
            luck=3.2,
        )

        assert stats.name == "Los Angeles Dodgers"
        assert stats.batting_runs == 45.2
        assert stats.home_run_rate == 0.045
        assert stats.baserunning_runs == 8.5
        assert stats.bullpen_xfip == 3.85
        assert stats.defensive_runs == 12.3
        assert stats.payroll == 285.6
        assert stats.age == 28.5
        assert stats.luck == 3.2

    def test_low_payroll_team_stats(self) -> None:
        """Test team statistics for a low payroll team."""
        stats = TeamStats(
            name="Pittsburgh Pirates",
            batting_runs=-35.8,
            home_run_rate=0.028,
            baserunning_runs=-12.1,
            bullpen_xfip=4.85,
            defensive_runs=-8.7,
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
                home_run_rate=0.045,
                baserunning_runs=8.5,
                bullpen_xfip=3.85,
                defensive_runs=12.3,
                payroll=285.6,
                age=28.5,
                luck=3.2,
            )

    def test_batting_runs_validation(self) -> None:
        """Test batting runs validation."""
        with pytest.raises(
            ValueError, match="Batting runs must be between -200.0 and 200.0"
        ):
            TeamStats(
                name="Bad Team",
                batting_runs=250.0,  # Too high
                home_run_rate=0.045,
                baserunning_runs=8.5,
                bullpen_xfip=3.85,
                defensive_runs=12.3,
                payroll=285.6,
                age=28.5,
                luck=3.2,
            )

    def test_home_run_rate_validation(self) -> None:
        """Test home run rate validation."""
        with pytest.raises(
            ValueError, match="Home run rate must be between 0.0 and 0.15"
        ):
            TeamStats(
                name="Bad Team",
                batting_runs=45.2,
                home_run_rate=0.2,  # Too high
                baserunning_runs=8.5,
                bullpen_xfip=3.85,
                defensive_runs=12.3,
                payroll=285.6,
                age=28.5,
                luck=3.2,
            )

    def test_baserunning_runs_validation(self) -> None:
        """Test baserunning runs validation."""
        with pytest.raises(
            ValueError, match="Baserunning runs must be between -50.0 and 50.0"
        ):
            TeamStats(
                name="Bad Team",
                batting_runs=45.2,
                home_run_rate=0.045,
                baserunning_runs=-75.0,  # Too low
                bullpen_xfip=3.85,
                defensive_runs=12.3,
                payroll=285.6,
                age=28.5,
                luck=3.2,
            )

    def test_bullpen_xfip_validation(self) -> None:
        """Test bullpen xFIP validation."""
        with pytest.raises(
            ValueError, match="Bullpen xFIP must be between 2.0 and 8.0"
        ):
            TeamStats(
                name="Bad Team",
                batting_runs=45.2,
                home_run_rate=0.045,
                baserunning_runs=8.5,
                bullpen_xfip=9.0,  # Too high
                defensive_runs=12.3,
                payroll=285.6,
                age=28.5,
                luck=3.2,
            )

    def test_defensive_runs_validation(self) -> None:
        """Test defensive runs validation."""
        with pytest.raises(
            ValueError, match="Defensive runs must be between -100.0 and 100.0"
        ):
            TeamStats(
                name="Bad Team",
                batting_runs=45.2,
                home_run_rate=0.045,
                baserunning_runs=8.5,
                bullpen_xfip=3.85,
                defensive_runs=150.0,  # Too high
                payroll=285.6,
                age=28.5,
                luck=3.2,
            )

    def test_payroll_validation(self) -> None:
        """Test payroll validation."""
        with pytest.raises(
            ValueError, match="Payroll must be between 30.0 and 500.0 million"
        ):
            TeamStats(
                name="Bad Team",
                batting_runs=45.2,
                home_run_rate=0.045,
                baserunning_runs=8.5,
                bullpen_xfip=3.85,
                defensive_runs=12.3,
                payroll=25.0,  # Too low
                age=28.5,
                luck=3.2,
            )

    def test_age_validation(self) -> None:
        """Test team age validation."""
        with pytest.raises(
            ValueError, match="Team age must be between 20.0 and 40.0 years"
        ):
            TeamStats(
                name="Bad Team",
                batting_runs=45.2,
                home_run_rate=0.045,
                baserunning_runs=8.5,
                bullpen_xfip=3.85,
                defensive_runs=12.3,
                payroll=285.6,
                age=45.0,  # Too old
                luck=3.2,
            )

    def test_luck_validation(self) -> None:
        """Test luck validation."""
        with pytest.raises(ValueError, match="Luck must be between -30.0 and 30.0"):
            TeamStats(
                name="Bad Team",
                batting_runs=45.2,
                home_run_rate=0.045,
                baserunning_runs=8.5,
                bullpen_xfip=3.85,
                defensive_runs=12.3,
                payroll=285.6,
                age=28.5,
                luck=40.0,  # Too high
            )


class TestTeamNerdStats:
    """Test cases for TeamNerdStats data structure."""

    def create_sample_team_stats(self) -> TeamStats:
        """Create sample team statistics for testing."""
        return TeamStats(
            name="Test Team",
            batting_runs=25.0,
            home_run_rate=0.040,
            baserunning_runs=5.0,
            bullpen_xfip=4.20,
            defensive_runs=8.0,
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
            z_home_run_rate=0.5,
            z_baserunning_runs=0.3,
            z_bullpen_xfip=-0.2,
            z_defensive_runs=0.6,
            z_payroll=0.4,
            z_age=-0.3,
            adjusted_payroll=0.0,
            adjusted_age=0.3,
            adjusted_luck=2.0,
            tnerd_score=8.5,
        )

        assert nerd_stats.team_stats == team_stats
        assert nerd_stats.z_batting_runs == 0.8
        assert nerd_stats.z_home_run_rate == 0.5
        assert nerd_stats.z_baserunning_runs == 0.3
        assert nerd_stats.z_bullpen_xfip == -0.2
        assert nerd_stats.z_defensive_runs == 0.6
        assert nerd_stats.z_payroll == 0.4
        assert nerd_stats.z_age == -0.3
        assert nerd_stats.adjusted_payroll == 0.0
        assert nerd_stats.adjusted_age == 0.3
        assert nerd_stats.adjusted_luck == 2.0
        assert nerd_stats.tnerd_score == 8.5

    def test_z_score_validation(self) -> None:
        """Test z-score validation."""
        team_stats = self.create_sample_team_stats()

        with pytest.raises(ValueError, match="Z-score must be between -10.0 and 10.0"):
            TeamNerdStats(
                team_stats=team_stats,
                z_batting_runs=12.0,  # Too high
                z_home_run_rate=0.5,
                z_baserunning_runs=0.3,
                z_bullpen_xfip=-0.2,
                z_defensive_runs=0.6,
                z_payroll=0.4,
                z_age=-0.3,
                adjusted_payroll=0.0,
                adjusted_age=0.3,
                adjusted_luck=2.0,
                tnerd_score=8.5,
            )

    def test_adjusted_payroll_validation(self) -> None:
        """Test adjusted payroll validation."""
        team_stats = self.create_sample_team_stats()

        with pytest.raises(
            ValueError, match="Adjusted payroll must be between 0.0 and 10.0"
        ):
            TeamNerdStats(
                team_stats=team_stats,
                z_batting_runs=0.8,
                z_home_run_rate=0.5,
                z_baserunning_runs=0.3,
                z_bullpen_xfip=-0.2,
                z_defensive_runs=0.6,
                z_payroll=0.4,
                z_age=-0.3,
                adjusted_payroll=-0.5,  # Too low
                adjusted_age=0.3,
                adjusted_luck=2.0,
                tnerd_score=8.5,
            )

    def test_adjusted_age_validation(self) -> None:
        """Test adjusted age validation."""
        team_stats = self.create_sample_team_stats()

        with pytest.raises(
            ValueError, match="Adjusted age must be between 0.0 and 10.0"
        ):
            TeamNerdStats(
                team_stats=team_stats,
                z_batting_runs=0.8,
                z_home_run_rate=0.5,
                z_baserunning_runs=0.3,
                z_bullpen_xfip=-0.2,
                z_defensive_runs=0.6,
                z_payroll=0.4,
                z_age=-0.3,
                adjusted_payroll=0.0,
                adjusted_age=15.0,  # Too high
                adjusted_luck=2.0,
                tnerd_score=8.5,
            )

    def test_adjusted_luck_validation(self) -> None:
        """Test adjusted luck validation."""
        team_stats = self.create_sample_team_stats()

        with pytest.raises(
            ValueError, match="Adjusted luck must be between 0.0 and 2.0"
        ):
            TeamNerdStats(
                team_stats=team_stats,
                z_batting_runs=0.8,
                z_home_run_rate=0.5,
                z_baserunning_runs=0.3,
                z_bullpen_xfip=-0.2,
                z_defensive_runs=0.6,
                z_payroll=0.4,
                z_age=-0.3,
                adjusted_payroll=0.0,
                adjusted_age=0.3,
                adjusted_luck=3.0,  # Too high
                tnerd_score=8.5,
            )

    def test_tnerd_score_validation(self) -> None:
        """Test tNERD score validation."""
        team_stats = self.create_sample_team_stats()

        with pytest.raises(
            ValueError, match="tNERD score must be between 0.0 and 50.0"
        ):
            TeamNerdStats(
                team_stats=team_stats,
                z_batting_runs=0.8,
                z_home_run_rate=0.5,
                z_baserunning_runs=0.3,
                z_bullpen_xfip=-0.2,
                z_defensive_runs=0.6,
                z_payroll=0.4,
                z_age=-0.3,
                adjusted_payroll=0.0,
                adjusted_age=0.3,
                adjusted_luck=2.0,
                tnerd_score=75.0,  # Too high
            )


class TestCalculateTnerdScore:
    """Test cases for tNERD score calculation."""

    def create_sample_league_stats(self) -> tuple[dict[str, float], dict[str, float]]:
        """Create sample league statistics for testing."""
        league_means = {
            "batting_runs": 0.0,
            "home_run_rate": 0.035,
            "baserunning_runs": 0.0,
            "bullpen_xfip": 4.20,
            "defensive_runs": 0.0,
            "payroll": 140.0,
            "age": 28.5,
        }

        league_std_devs = {
            "batting_runs": 30.0,
            "home_run_rate": 0.008,
            "baserunning_runs": 15.0,
            "bullpen_xfip": 0.40,
            "defensive_runs": 20.0,
            "payroll": 50.0,
            "age": 1.5,
        }

        return league_means, league_std_devs

    def test_calculate_tnerd_score_basic(self) -> None:
        """Test basic tNERD score calculation."""
        team_stats = TeamStats(
            name="Test Team",
            batting_runs=30.0,  # Above average
            home_run_rate=0.043,  # Above average
            baserunning_runs=15.0,  # Above average
            bullpen_xfip=3.80,  # Better than average (lower is better)
            defensive_runs=20.0,  # Above average
            payroll=90.0,  # Below average (better for tNERD)
            age=26.0,  # Younger than average (better)
            luck=4.0,  # Lucky
        )

        league_means, league_std_devs = self.create_sample_league_stats()

        nerd_stats = calculate_tnerd_score(team_stats, league_means, league_std_devs)

        # Check that z-scores are calculated correctly
        assert nerd_stats.z_batting_runs == (30.0 - 0.0) / 30.0  # 1.0
        assert nerd_stats.z_home_run_rate == (0.043 - 0.035) / 0.008  # 1.0
        assert nerd_stats.z_baserunning_runs == (15.0 - 0.0) / 15.0  # 1.0
        assert nerd_stats.z_bullpen_xfip == (3.80 - 4.20) / 0.40  # -1.0
        assert nerd_stats.z_defensive_runs == (20.0 - 0.0) / 20.0  # 1.0
        assert nerd_stats.z_payroll == (90.0 - 140.0) / 50.0  # -1.0
        assert nerd_stats.z_age == (26.0 - 28.5) / 1.5  # -1.67 (approximately)

        # Check adjusted values
        assert (
            nerd_stats.adjusted_payroll == 1.0
        )  # -z_payroll = -(-1.0) = 1.0, below average is better
        assert (
            abs(nerd_stats.adjusted_age - 1.67) < 0.01
        )  # -z_age = -(-1.67) = 1.67, younger is better
        assert nerd_stats.adjusted_luck == 2.0  # luck is 4.0, capped at 2.0

        # Check tNERD score calculation
        expected_tnerd = (
            1.0  # z_batting_runs
            + 1.0  # z_home_run_rate
            + 1.0  # z_baserunning_runs
            + (-1.0 / 2)  # z_bullpen_xfip / 2
            + (1.0 / 2)  # z_defensive_runs / 2
            + 1.0  # adjusted_payroll
            + 1.67  # adjusted_age (approximately)
            + (2.0 / 2)  # adjusted_luck / 2
            + 4.0  # constant
        )

        assert abs(nerd_stats.tnerd_score - expected_tnerd) < 0.01

    def test_calculate_tnerd_score_negative_adjustments(self) -> None:
        """Test that negative values are set to zero for payroll, age, and luck."""
        team_stats = TeamStats(
            name="Negative Team",
            batting_runs=-45.0,
            home_run_rate=0.025,
            baserunning_runs=-20.0,
            bullpen_xfip=5.00,  # Worse than average
            defensive_runs=-30.0,
            payroll=200.0,  # Above average (worse for tNERD)
            age=31.0,  # Older than average (worse)
            luck=-8.0,  # Unlucky
        )

        league_means, league_std_devs = self.create_sample_league_stats()

        nerd_stats = calculate_tnerd_score(team_stats, league_means, league_std_devs)

        # Check that negative values are set to zero
        assert nerd_stats.adjusted_payroll == 0.0  # -z_payroll is negative
        assert nerd_stats.adjusted_age == 0.0  # -z_age is negative
        assert nerd_stats.adjusted_luck == 0.0  # luck is negative

    def test_calculate_tnerd_score_luck_cap(self) -> None:
        """Test that luck is properly capped at 2.0."""
        team_stats = TeamStats(
            name="Very Lucky Team",
            batting_runs=0.0,
            home_run_rate=0.035,
            baserunning_runs=0.0,
            bullpen_xfip=4.20,
            defensive_runs=0.0,
            payroll=140.0,
            age=28.5,
            luck=15.0,  # Very lucky
        )

        league_means, league_std_devs = self.create_sample_league_stats()

        nerd_stats = calculate_tnerd_score(team_stats, league_means, league_std_devs)

        # Check that luck is capped at 2.0
        assert nerd_stats.adjusted_luck == 2.0

    def test_calculate_tnerd_score_all_average(self) -> None:
        """Test tNERD score calculation with all average values."""
        team_stats = TeamStats(
            name="Average Team",
            batting_runs=0.0,  # League average
            home_run_rate=0.035,  # League average
            baserunning_runs=0.0,  # League average
            bullpen_xfip=4.20,  # League average
            defensive_runs=0.0,  # League average
            payroll=140.0,  # League average
            age=28.5,  # League average
            luck=0.0,  # No luck
        )

        league_means, league_std_devs = self.create_sample_league_stats()

        nerd_stats = calculate_tnerd_score(team_stats, league_means, league_std_devs)

        # All z-scores should be 0.0
        assert nerd_stats.z_batting_runs == 0.0
        assert nerd_stats.z_home_run_rate == 0.0
        assert nerd_stats.z_baserunning_runs == 0.0
        assert nerd_stats.z_bullpen_xfip == 0.0
        assert nerd_stats.z_defensive_runs == 0.0
        assert nerd_stats.z_payroll == 0.0
        assert nerd_stats.z_age == 0.0

        # All adjusted values should be 0.0
        assert nerd_stats.adjusted_payroll == 0.0
        assert nerd_stats.adjusted_age == 0.0
        assert nerd_stats.adjusted_luck == 0.0

        # tNERD score should be just the constant
        assert nerd_stats.tnerd_score == 4.0
