"""Pitcher statistics data structures for pNERD calculation."""

from dataclasses import dataclass


@dataclass
class PitcherStats:
    """
    Data structure for pitcher statistics used in pNERD calculation.

    Based on FanGraphs Game NERD methodology, these statistics are used
    to calculate pitcher NERD scores (pNERD).
    """

    name: str
    team: str
    xfip_minus: float  # xFIP- (lower is better)
    swinging_strike_rate: float  # SwStr% (higher is better)
    strike_rate: float  # Strike% (higher is better)
    velocity: float  # Average fastball velocity in mph (higher is better)
    age: int  # Age in years
    pace: float  # Pace between pitches in seconds (lower is better)
    luck: float  # ERA- minus xFIP- (can be positive or negative)
    knuckleball_rate: float  # KN% (higher is better)

    def __post_init__(self) -> None:
        """Validate pitcher statistics after initialization."""
        self._validate_stats()

    def _validate_stats(self) -> None:
        """Validate that all statistics are within reasonable ranges."""

        # Name and team validation
        if not self.name or not self.name.strip():
            raise ValueError("Pitcher name cannot be empty")
        if not self.team or not self.team.strip():
            raise ValueError("Team cannot be empty")

        # xFIP- validation (typically 50-150, where 100 is league average)
        if not 0 <= self.xfip_minus <= 300:
            raise ValueError(f"xFIP- must be between 0 and 300, got {self.xfip_minus}")

        # Swinging strike rate validation (typically 0.05-0.20)
        if not 0.0 <= self.swinging_strike_rate <= 1.0:
            raise ValueError(
                f"Swinging strike rate must be between 0.0 and 1.0, got {self.swinging_strike_rate}"
            )

        # Strike rate validation (typically 0.50-0.80)
        if not 0.0 <= self.strike_rate <= 1.0:
            raise ValueError(
                f"Strike rate must be between 0.0 and 1.0, got {self.strike_rate}"
            )

        # Velocity validation (typically 85-105 mph)
        if not 70.0 <= self.velocity <= 110.0:
            raise ValueError(
                f"Velocity must be between 70.0 and 110.0 mph, got {self.velocity}"
            )

        # Age validation (typically 20-45 years)
        if not 18 <= self.age <= 50:
            raise ValueError(f"Age must be between 18 and 50 years, got {self.age}")

        # Pace validation (typically 15-30 seconds)
        if not 10.0 <= self.pace <= 40.0:
            raise ValueError(
                f"Pace must be between 10.0 and 40.0 seconds, got {self.pace}"
            )

        # Luck validation (can be negative - no strict bounds)
        if not -100.0 <= self.luck <= 100.0:
            raise ValueError(f"Luck must be between -100.0 and 100.0, got {self.luck}")

        # Knuckleball rate validation (typically 0.0-1.0, but most pitchers have 0.0)
        if not 0.0 <= self.knuckleball_rate <= 1.0:
            raise ValueError(
                f"Knuckleball rate must be between 0.0 and 1.0, got {self.knuckleball_rate}"
            )


@dataclass
class PitcherNerdStats:
    """
    Data structure for calculated pitcher NERD statistics.

    Contains z-scores and adjusted values used in pNERD calculation.
    """

    pitcher_stats: PitcherStats

    # Z-scores (standard deviations from mean)
    z_xfip_minus: float
    z_swinging_strike_rate: float
    z_strike_rate: float
    z_velocity: float
    z_age: float
    z_pace: float

    # Adjusted values (after caps and positive-only rules)
    adjusted_velocity: float  # Capped at 2.0, positive only
    adjusted_age: float  # Capped at 2.0, positive only
    adjusted_luck: float  # Capped at 1.0, positive only

    # Final pNERD score
    pnerd_score: float

    def __post_init__(self) -> None:
        """Validate NERD statistics after initialization."""
        self._validate_nerd_stats()

    def _validate_nerd_stats(self) -> None:
        """Validate that all NERD statistics are reasonable."""

        # Z-scores should typically be within -3 to +3 standard deviations, but allow extreme values
        z_scores = [
            self.z_xfip_minus,
            self.z_swinging_strike_rate,
            self.z_strike_rate,
            self.z_velocity,
            self.z_age,
            self.z_pace,
        ]

        for z_score in z_scores:
            if not -10.0 <= z_score <= 10.0:
                raise ValueError(
                    f"Z-score must be between -10.0 and 10.0, got {z_score}"
                )

        # Adjusted values validation
        if not 0.0 <= self.adjusted_velocity <= 2.0:
            raise ValueError(
                f"Adjusted velocity must be between 0.0 and 2.0, got {self.adjusted_velocity}"
            )

        if not 0.0 <= self.adjusted_age <= 2.0:
            raise ValueError(
                f"Adjusted age must be between 0.0 and 2.0, got {self.adjusted_age}"
            )

        if not 0.0 <= self.adjusted_luck <= 1.0:
            raise ValueError(
                f"Adjusted luck must be between 0.0 and 1.0, got {self.adjusted_luck}"
            )

        # pNERD score should be positive (typically 0-20)
        if not 0.0 <= self.pnerd_score <= 50.0:
            raise ValueError(
                f"pNERD score must be between 0.0 and 50.0, got {self.pnerd_score}"
            )


def calculate_pnerd_score(
    pitcher_stats: PitcherStats,
    league_means: dict[str, float],
    league_std_devs: dict[str, float],
    constant: float = 3.8,
) -> PitcherNerdStats:
    """
    Calculate pNERD score for a pitcher.

    Formula: (zxFIP- * 2) + (zSwStrk / 2) + (zStrk / 2) + zVelo + zAge + (zPace / 2) + (Luck / 20) + (KN * 5) + Constant

    Args:
        pitcher_stats: Pitcher statistics
        league_means: Dictionary of league mean values for each stat
        league_std_devs: Dictionary of league standard deviations for each stat
        constant: Constant value (default 3.8)

    Returns:
        PitcherNerdStats with calculated z-scores and pNERD score
    """

    # Calculate z-scores
    z_xfip_minus = (
        pitcher_stats.xfip_minus - league_means["xfip_minus"]
    ) / league_std_devs["xfip_minus"]
    z_swinging_strike_rate = (
        pitcher_stats.swinging_strike_rate - league_means["swinging_strike_rate"]
    ) / league_std_devs["swinging_strike_rate"]
    z_strike_rate = (
        pitcher_stats.strike_rate - league_means["strike_rate"]
    ) / league_std_devs["strike_rate"]
    z_velocity = (pitcher_stats.velocity - league_means["velocity"]) / league_std_devs[
        "velocity"
    ]
    z_age = (pitcher_stats.age - league_means["age"]) / league_std_devs["age"]
    z_pace = (pitcher_stats.pace - league_means["pace"]) / league_std_devs["pace"]

    # Apply caps and positive-only rules
    adjusted_velocity = max(0.0, min(2.0, z_velocity))
    # For age, younger is better, so we want negative z_age values (below mean age)
    # We flip the sign and then apply caps and positive-only rules
    adjusted_age = max(0.0, min(2.0, -z_age))
    adjusted_luck = max(0.0, min(1.0, pitcher_stats.luck))

    # Calculate pNERD score using the formula
    pnerd_score = (
        (z_xfip_minus * 2)
        + (z_swinging_strike_rate / 2)
        + (z_strike_rate / 2)
        + adjusted_velocity
        + adjusted_age
        + (z_pace / 2)
        + (adjusted_luck / 20)
        + (pitcher_stats.knuckleball_rate * 5)
        + constant
    )

    return PitcherNerdStats(
        pitcher_stats=pitcher_stats,
        z_xfip_minus=z_xfip_minus,
        z_swinging_strike_rate=z_swinging_strike_rate,
        z_strike_rate=z_strike_rate,
        z_velocity=z_velocity,
        z_age=z_age,
        z_pace=z_pace,
        adjusted_velocity=adjusted_velocity,
        adjusted_age=adjusted_age,
        adjusted_luck=adjusted_luck,
        pnerd_score=pnerd_score,
    )
