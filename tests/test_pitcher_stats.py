"""Unit tests for pitcher statistics data structures."""

import pytest

from mlb_watchability.pitcher_stats import (
    PitcherNerdStats,
    PitcherStats,
    calculate_pnerd_score,
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

    def test_xfip_minus_validation(self) -> None:
        """Test xFIP- validation."""
        with pytest.raises(ValueError, match="xFIP- must be between 0 and 300"):
            PitcherStats(
                name="Bad Pitcher",
                team="BAD",
                xfip_minus=350,  # Too high
                swinging_strike_rate=0.15,
                strike_rate=0.65,
                velocity=95.5,
                age=34,
                pace=18.2,
                luck=-5.0,
                knuckleball_rate=0.0,
            )

    def test_swinging_strike_rate_validation(self) -> None:
        """Test swinging strike rate validation."""
        with pytest.raises(
            ValueError, match="Swinging strike rate must be between 0.0 and 1.0"
        ):
            PitcherStats(
                name="Bad Pitcher",
                team="BAD",
                xfip_minus=85,
                swinging_strike_rate=1.5,  # Too high
                strike_rate=0.65,
                velocity=95.5,
                age=34,
                pace=18.2,
                luck=-5.0,
                knuckleball_rate=0.0,
            )

    def test_strike_rate_validation(self) -> None:
        """Test strike rate validation."""
        with pytest.raises(ValueError, match="Strike rate must be between 0.0 and 1.0"):
            PitcherStats(
                name="Bad Pitcher",
                team="BAD",
                xfip_minus=85,
                swinging_strike_rate=0.15,
                strike_rate=-0.1,  # Too low
                velocity=95.5,
                age=34,
                pace=18.2,
                luck=-5.0,
                knuckleball_rate=0.0,
            )

    def test_velocity_validation(self) -> None:
        """Test velocity validation."""
        with pytest.raises(
            ValueError, match="Velocity must be between 70.0 and 110.0 mph"
        ):
            PitcherStats(
                name="Bad Pitcher",
                team="BAD",
                xfip_minus=85,
                swinging_strike_rate=0.15,
                strike_rate=0.65,
                velocity=65.0,  # Too low
                age=34,
                pace=18.2,
                luck=-5.0,
                knuckleball_rate=0.0,
            )

    def test_age_validation(self) -> None:
        """Test age validation."""
        with pytest.raises(ValueError, match="Age must be between 18 and 50 years"):
            PitcherStats(
                name="Bad Pitcher",
                team="BAD",
                xfip_minus=85,
                swinging_strike_rate=0.15,
                strike_rate=0.65,
                velocity=95.5,
                age=55,  # Too old
                pace=18.2,
                luck=-5.0,
                knuckleball_rate=0.0,
            )

    def test_pace_validation(self) -> None:
        """Test pace validation."""
        with pytest.raises(
            ValueError, match="Pace must be between 10.0 and 40.0 seconds"
        ):
            PitcherStats(
                name="Bad Pitcher",
                team="BAD",
                xfip_minus=85,
                swinging_strike_rate=0.15,
                strike_rate=0.65,
                velocity=95.5,
                age=34,
                pace=5.0,  # Too fast
                luck=-5.0,
                knuckleball_rate=0.0,
            )

    def test_luck_validation(self) -> None:
        """Test luck validation."""
        with pytest.raises(ValueError, match="Luck must be between -100.0 and 200.0"):
            PitcherStats(
                name="Bad Pitcher",
                team="BAD",
                xfip_minus=85,
                swinging_strike_rate=0.15,
                strike_rate=0.65,
                velocity=95.5,
                age=34,
                pace=18.2,
                luck=250.0,  # Too high
                knuckleball_rate=0.0,
            )

    def test_knuckleball_rate_validation(self) -> None:
        """Test knuckleball rate validation."""
        with pytest.raises(
            ValueError, match="Knuckleball rate must be between 0.0 and 1.0"
        ):
            PitcherStats(
                name="Bad Pitcher",
                team="BAD",
                xfip_minus=85,
                swinging_strike_rate=0.15,
                strike_rate=0.65,
                velocity=95.5,
                age=34,
                pace=18.2,
                luck=-5.0,
                knuckleball_rate=1.5,  # Too high
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

    def test_z_score_validation(self) -> None:
        """Test z-score validation."""
        pitcher_stats = self.create_sample_pitcher_stats()

        with pytest.raises(ValueError, match="Z-score must be between -10.0 and 10.0"):
            PitcherNerdStats(
                pitcher_stats=pitcher_stats,
                z_xfip_minus=11.0,  # Too high
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
            ValueError, match="pNERD score must be between 0.0 and 50.0"
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
            (-1.0 * 2)  # z_xfip_minus * 2
            + (1.0 / 2)  # z_swinging_strike_rate / 2
            + (1.0 / 2)  # z_strike_rate / 2
            + 1.0  # adjusted_velocity
            + 0.75  # adjusted_age
            + (-1.0 / 2)  # z_pace / 2
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
