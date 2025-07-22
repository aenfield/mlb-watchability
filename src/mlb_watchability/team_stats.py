"""Team statistics data structures for tNERD calculation."""

from dataclasses import dataclass

from scipy import stats  # type: ignore

from .data_retrieval import get_all_team_stats

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

    # Component values
    batting_component: float = 0.0
    barrel_component: float = 0.0
    baserunning_component: float = 0.0
    fielding_component: float = 0.0
    payroll_component: float = 0.0
    age_component: float = 0.0
    luck_component: float = 0.0
    constant_component: float = 0.0

    def __post_init__(self) -> None:
        """Validate NERD statistics after initialization."""
        self._validate_nerd_stats()

    @property
    def components(self) -> dict[str, float]:
        """Dictionary of all tNERD component values."""
        return {
            "batting": self.batting_component,
            "barrel": self.barrel_component,
            "baserunning": self.baserunning_component,
            "fielding": self.fielding_component,
            "payroll": self.payroll_component,
            "age": self.age_component,
            "luck": self.luck_component,
            "constant": self.constant_component,
        }

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

    # Calculate individual components (stored to avoid duplication)
    batting_component = z_batting_runs
    barrel_component = z_barrel_rate
    baserunning_component = z_baserunning_runs
    fielding_component = z_fielding_runs
    payroll_component = adjusted_payroll
    age_component = adjusted_age
    luck_component = adjusted_luck
    constant_component = constant

    # Calculate tNERD score using the components
    tnerd_score = (
        batting_component
        + barrel_component
        + baserunning_component
        + fielding_component
        + payroll_component
        + age_component
        + luck_component
        + constant_component
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
        batting_component=batting_component,
        barrel_component=barrel_component,
        baserunning_component=baserunning_component,
        fielding_component=fielding_component,
        payroll_component=payroll_component,
        age_component=age_component,
        luck_component=luck_component,
        constant_component=constant_component,
        tnerd_score=tnerd_score,
    )


def get_all_team_stats_objects(season: int = 2025) -> dict[str, TeamStats]:
    """
    Get all team statistics as TeamStats objects.

    Args:
        season: Season year (default: 2025)

    Returns:
        Dictionary mapping team names to TeamStats objects

    Raises:
        RuntimeError: If data retrieval fails
    """
    try:
        # Get raw team data
        raw_team_data = get_all_team_stats(season)

        # Create TeamStats objects from raw data
        team_stats_dict = {}
        for team_name, raw_stats in raw_team_data.items():
            team_stats = TeamStats(
                name=raw_stats["Team"],
                batting_runs=raw_stats["Bat"],
                barrel_rate=raw_stats["Barrel%"],
                baserunning_runs=raw_stats["BsR"],
                fielding_runs=raw_stats["Fld"],
                payroll=raw_stats["Payroll"],
                age=raw_stats["Payroll_Age"],
                luck=raw_stats["Luck"],
            )
            team_stats_dict[team_name] = team_stats

    except Exception as e:
        raise RuntimeError(
            f"Failed to create team stats objects for season {season}: {str(e)}"
        ) from e
    else:
        return team_stats_dict


def calculate_team_nerd_scores(season: int = 2025) -> dict[str, float]:
    """Calculate team NERD scores for all teams."""
    detailed_stats = calculate_detailed_team_nerd_scores(season)
    return {team: nerd_stats.tnerd_score for team, nerd_stats in detailed_stats.items()}


def calculate_detailed_team_nerd_scores(season: int = 2025) -> dict[str, TeamNerdStats]:
    """Calculate detailed team NERD scores for all teams."""
    try:
        # Get all team stats - note: payroll data is only available for 2025
        # For other years, we'll use the team batting stats for that year but 2025 payroll/age data
        team_stats_dict = get_all_team_stats_objects(season)

        # Calculate league means and standard deviations
        all_teams = list(team_stats_dict.values())

        # Extract values for each stat
        batting_runs = [team.batting_runs for team in all_teams]
        barrel_rates = [team.barrel_rate for team in all_teams]
        baserunning_runs = [team.baserunning_runs for team in all_teams]
        fielding_runs = [team.fielding_runs for team in all_teams]
        payrolls = [team.payroll for team in all_teams]
        ages = [team.age for team in all_teams]
        luck_values = [team.luck for team in all_teams]

        # Calculate means and standard deviations
        league_means = {
            "batting_runs": stats.tmean(batting_runs),
            "barrel_rate": stats.tmean(barrel_rates),
            "baserunning_runs": stats.tmean(baserunning_runs),
            "fielding_runs": stats.tmean(fielding_runs),
            "payroll": stats.tmean(payrolls),
            "age": stats.tmean(ages),
            "luck": stats.tmean(luck_values),
        }

        league_std_devs = {
            "batting_runs": stats.tstd(batting_runs),
            "barrel_rate": stats.tstd(barrel_rates),
            "baserunning_runs": stats.tstd(baserunning_runs),
            "fielding_runs": stats.tstd(fielding_runs),
            "payroll": stats.tstd(payrolls),
            "age": stats.tstd(ages),
            "luck": stats.tstd(luck_values),
        }

        # Calculate tNERD for each team
        team_nerd_details = {}
        for team_abbr, team_stats in team_stats_dict.items():
            try:
                team_nerd_stats = calculate_tnerd_score(
                    team_stats, league_means, league_std_devs
                )
                team_nerd_details[team_abbr] = team_nerd_stats
            except ValueError:
                # Skip teams with invalid tNERD scores (negative values)
                continue

    except Exception:
        # If calculation fails, return empty dict
        return {}
    else:
        return team_nerd_details
