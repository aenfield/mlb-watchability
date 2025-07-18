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
    barrel_rate: float  # Barrel % (Barrel%)
    baserunning_runs: float  # Baserunning Runs (BsR)
    fielding_runs: float  # Fielding Runs Above Average (Fld)
    payroll: float  # Payroll, Where Below Average Is Better (Pay)
    age: float  # Batter Age, Where Younger Is Better (Age)
    luck: float  # wRC minus Runs (Luck)

    def __post_init__(self) -> None:
        """Validate team statistics after initialization."""
        self._validate_stats()

    def _validate_stats(self) -> None:
        """Validate that all statistics are within reasonable ranges."""

        # Name validation
        if not self.name or not self.name.strip():
            raise ValueError("Team name cannot be empty")


@dataclass
class TeamNerdStats:
    """
    Data structure for calculated team NERD statistics.

    Contains z-scores and adjusted values used in tNERD calculation.
    """

    team_stats: TeamStats

    # Z-scores (standard deviations from mean)
    z_batting_runs: float
    z_barrel_rate: float
    z_baserunning_runs: float
    z_fielding_runs: float
    z_payroll: float
    z_age: float
    z_luck: float

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

    Formula: zBat + zBarrel% + zBsR + zFld + zPay + zAge + zLuck + Constant

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
    z_barrel_rate = (
        team_stats.barrel_rate - league_means["barrel_rate"]
    ) / league_std_devs["barrel_rate"]
    z_baserunning_runs = (
        team_stats.baserunning_runs - league_means["baserunning_runs"]
    ) / league_std_devs["baserunning_runs"]
    z_fielding_runs = (
        team_stats.fielding_runs - league_means["fielding_runs"]
    ) / league_std_devs["fielding_runs"]
    z_payroll = (team_stats.payroll - league_means["payroll"]) / league_std_devs[
        "payroll"
    ]
    z_age = (team_stats.age - league_means["age"]) / league_std_devs["age"]
    z_luck = (team_stats.luck - league_means["luck"]) / league_std_devs["luck"]

    # Apply caps and positive-only rules
    # For payroll, below average is better, so we want negative z_payroll values
    # We flip the sign and then apply positive-only rules
    adjusted_payroll = max(0.0, -z_payroll)
    # For age, younger is better, so we want negative z_age values (below mean age)
    # We flip the sign and then apply positive-only rules
    adjusted_age = max(0.0, -z_age)
    # For luck, apply positive-only rule and cap at 2.0
    adjusted_luck = max(0.0, min(2.0, z_luck))

    # Calculate tNERD score using the formula
    tnerd_score = (
        z_batting_runs
        + z_barrel_rate
        + z_baserunning_runs
        + z_fielding_runs
        + adjusted_payroll
        + adjusted_age
        + adjusted_luck
        + constant
    )

    return TeamNerdStats(
        team_stats=team_stats,
        z_batting_runs=z_batting_runs,
        z_barrel_rate=z_barrel_rate,
        z_baserunning_runs=z_baserunning_runs,
        z_fielding_runs=z_fielding_runs,
        z_payroll=z_payroll,
        z_age=z_age,
        z_luck=z_luck,
        adjusted_payroll=adjusted_payroll,
        adjusted_age=adjusted_age,
        adjusted_luck=adjusted_luck,
        tnerd_score=tnerd_score,
    )
