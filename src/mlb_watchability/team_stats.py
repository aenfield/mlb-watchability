"""Team statistics data structures for tNERD calculation."""

from dataclasses import dataclass

# we skip ruff linting for magic values a bunch of places below with noqa for PLR2004, since it's
# clearer and less verbose and we don't need to use these checks in other places


@dataclass
class TeamStats:
    """
    Data structure for team statistics used in tNERD calculation.

    Based on FanGraphs Game NERD methodology, these statistics are used
    to calculate team NERD scores (tNERD).
    """

    name: str
    batting_runs: float  # Park-Adjusted Batting Runs Above Average (Bat)
    home_run_rate: float  # Park-Adjusted Home Run Rate (HR%)
    baserunning_runs: float  # Baserunning Runs (BsR)
    bullpen_xfip: float  # Bullpen xFIP (Bull)
    defensive_runs: float  # Defensive Runs (Def)
    payroll: float  # Payroll, Where Below Average Is Better (Pay)
    age: float  # Batter Age, Where Younger Is Better (Age)
    luck: float  # Expected Wins, Per WAR, Minus Actual Wins (Luck)

    def __post_init__(self) -> None:
        """Validate team statistics after initialization."""
        self._validate_stats()

    def _validate_stats(self) -> None:
        """Validate that all statistics are within reasonable ranges."""

        # Name validation
        if not self.name or not self.name.strip():
            raise ValueError("Team name cannot be empty")

        # Batting runs validation (typically -100 to +100 runs above/below average)
        if not -200.0 <= self.batting_runs <= 200.0:  # noqa: PLR2004
            raise ValueError(
                f"Batting runs must be between -200.0 and 200.0, got {self.batting_runs}"
            )

        # Home run rate validation (typically 0.02-0.08)
        if not 0.0 <= self.home_run_rate <= 0.15:  # noqa: PLR2004
            raise ValueError(
                f"Home run rate must be between 0.0 and 0.15, got {self.home_run_rate}"
            )

        # Baserunning runs validation (typically -30 to +30 runs)
        if not -50.0 <= self.baserunning_runs <= 50.0:  # noqa: PLR2004
            raise ValueError(
                f"Baserunning runs must be between -50.0 and 50.0, got {self.baserunning_runs}"
            )

        # Bullpen xFIP validation (typically 3.00-6.00)
        if not 2.0 <= self.bullpen_xfip <= 8.0:  # noqa: PLR2004
            raise ValueError(
                f"Bullpen xFIP must be between 2.0 and 8.0, got {self.bullpen_xfip}"
            )

        # Defensive runs validation (typically -50 to +50 runs)
        if not -100.0 <= self.defensive_runs <= 100.0:  # noqa: PLR2004
            raise ValueError(
                f"Defensive runs must be between -100.0 and 100.0, got {self.defensive_runs}"
            )

        # Payroll validation (typically in millions, 50-300)
        if not 30.0 <= self.payroll <= 500.0:  # noqa: PLR2004
            raise ValueError(
                f"Payroll must be between 30.0 and 500.0 million, got {self.payroll}"
            )

        # Age validation (typically 24-32 years average)
        if not 20.0 <= self.age <= 40.0:  # noqa: PLR2004
            raise ValueError(
                f"Team age must be between 20.0 and 40.0 years, got {self.age}"
            )

        # Luck validation (can be negative - expected wins minus actual wins)
        if not -30.0 <= self.luck <= 30.0:  # noqa: PLR2004
            raise ValueError(f"Luck must be between -30.0 and 30.0, got {self.luck}")


@dataclass
class TeamNerdStats:
    """
    Data structure for calculated team NERD statistics.

    Contains z-scores and adjusted values used in tNERD calculation.
    """

    team_stats: TeamStats

    # Z-scores (standard deviations from mean)
    z_batting_runs: float
    z_home_run_rate: float
    z_baserunning_runs: float
    z_bullpen_xfip: float
    z_defensive_runs: float
    z_payroll: float
    z_age: float

    # Adjusted values (after caps and positive-only rules)
    adjusted_payroll: float  # Positive only (below average is better)
    adjusted_age: float  # Positive only (younger is better)
    adjusted_luck: float  # Capped at 2.0, positive only

    # Final tNERD score
    tnerd_score: float

    def __post_init__(self) -> None:
        """Validate NERD statistics after initialization."""
        self._validate_nerd_stats()

    def _validate_nerd_stats(self) -> None:
        """Validate that all NERD statistics are reasonable."""

        # Z-scores should typically be within -3 to +3 standard deviations, but allow extreme values
        z_scores = [
            self.z_batting_runs,
            self.z_home_run_rate,
            self.z_baserunning_runs,
            self.z_bullpen_xfip,
            self.z_defensive_runs,
            self.z_payroll,
            self.z_age,
        ]

        for z_score in z_scores:
            if not -10.0 <= z_score <= 10.0:  # noqa: PLR2004
                raise ValueError(
                    f"Z-score must be between -10.0 and 10.0, got {z_score}"
                )

        # Adjusted values validation
        if not 0.0 <= self.adjusted_payroll <= 10.0:  # noqa: PLR2004
            raise ValueError(
                f"Adjusted payroll must be between 0.0 and 10.0, got {self.adjusted_payroll}"
            )

        if not 0.0 <= self.adjusted_age <= 10.0:  # noqa: PLR2004
            raise ValueError(
                f"Adjusted age must be between 0.0 and 10.0, got {self.adjusted_age}"
            )

        if not 0.0 <= self.adjusted_luck <= 2.0:  # noqa: PLR2004
            raise ValueError(
                f"Adjusted luck must be between 0.0 and 2.0, got {self.adjusted_luck}"
            )

        # tNERD score should be positive (typically 0-20)
        if not 0.0 <= self.tnerd_score <= 50.0:  # noqa: PLR2004
            raise ValueError(
                f"tNERD score must be between 0.0 and 50.0, got {self.tnerd_score}"
            )


def calculate_tnerd_score(
    team_stats: TeamStats,
    league_means: dict[str, float],
    league_std_devs: dict[str, float],
    constant: float = 4.0,
) -> TeamNerdStats:
    """
    Calculate tNERD score for a team.

    Formula: zBat + zHR% + zBsR + (zBull / 2) + (zDef / 2) + zPay + zAge + (Luck / 2) + Constant

    Args:
        team_stats: Team statistics
        league_means: Dictionary of league mean values for each stat
        league_std_devs: Dictionary of league standard deviations for each stat
        constant: Constant value (default 4.0)

    Returns:
        TeamNerdStats with calculated z-scores and tNERD score
    """

    # Calculate z-scores
    z_batting_runs = (
        team_stats.batting_runs - league_means["batting_runs"]
    ) / league_std_devs["batting_runs"]
    z_home_run_rate = (
        team_stats.home_run_rate - league_means["home_run_rate"]
    ) / league_std_devs["home_run_rate"]
    z_baserunning_runs = (
        team_stats.baserunning_runs - league_means["baserunning_runs"]
    ) / league_std_devs["baserunning_runs"]
    z_bullpen_xfip = (
        team_stats.bullpen_xfip - league_means["bullpen_xfip"]
    ) / league_std_devs["bullpen_xfip"]
    z_defensive_runs = (
        team_stats.defensive_runs - league_means["defensive_runs"]
    ) / league_std_devs["defensive_runs"]
    z_payroll = (team_stats.payroll - league_means["payroll"]) / league_std_devs[
        "payroll"
    ]
    z_age = (team_stats.age - league_means["age"]) / league_std_devs["age"]

    # Apply caps and positive-only rules
    # For payroll, below average is better, so we want negative z_payroll values
    # We flip the sign and then apply positive-only rules
    adjusted_payroll = max(0.0, -z_payroll)
    # For age, younger is better, so we want negative z_age values (below mean age)
    # We flip the sign and then apply positive-only rules
    adjusted_age = max(0.0, -z_age)
    adjusted_luck = max(0.0, min(2.0, team_stats.luck))

    # Calculate tNERD score using the formula
    tnerd_score = (
        z_batting_runs
        + z_home_run_rate
        + z_baserunning_runs
        + (z_bullpen_xfip / 2)
        + (z_defensive_runs / 2)
        + adjusted_payroll
        + adjusted_age
        + (adjusted_luck / 2)
        + constant
    )

    return TeamNerdStats(
        team_stats=team_stats,
        z_batting_runs=z_batting_runs,
        z_home_run_rate=z_home_run_rate,
        z_baserunning_runs=z_baserunning_runs,
        z_bullpen_xfip=z_bullpen_xfip,
        z_defensive_runs=z_defensive_runs,
        z_payroll=z_payroll,
        z_age=z_age,
        adjusted_payroll=adjusted_payroll,
        adjusted_age=adjusted_age,
        adjusted_luck=adjusted_luck,
        tnerd_score=tnerd_score,
    )
