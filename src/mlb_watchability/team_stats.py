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
    bullpen_runs: float  # Bullpen Runs Above Average (RAR)
    payroll: float  # Payroll, Where Below Average Is Better (Pay)
    age: float  # Batter Age, Where Younger Is Better (Age)
    luck: float  # wRC minus Runs (Luck)
    broadcaster_rating: float  # TV Broadcaster Rating (TV)
    radio_broadcaster_rating: float  # Radio Broadcaster Rating (Radio)

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
    z_bullpen_runs: float
    z_payroll: float
    z_age: float
    z_luck: float
    z_broadcaster_rating: float
    z_radio_broadcaster_rating: float

    # Adjusted values (after caps and positive-only rules)
    adjusted_payroll: float  # Positive only (below average is better)
    adjusted_age: float  # Positive only (younger is better)
    adjusted_luck: float  # Capped at 2.0, positive only
    adjusted_broadcaster_rating: float  # Positive only (higher is better)
    adjusted_radio_broadcaster_rating: float  # Positive only (higher is better)

    # Final tNERD score
    tnerd_score: float

    # Component values
    batting_component: float = 0.0
    barrel_component: float = 0.0
    baserunning_component: float = 0.0
    fielding_component: float = 0.0
    bullpen_component: float = 0.0
    payroll_component: float = 0.0
    age_component: float = 0.0
    luck_component: float = 0.0
    broadcaster_component: float = 0.0
    radio_broadcaster_component: float = 0.0
    constant_component: float = 0.0

    @classmethod
    def from_stats_and_means(
        cls,
        team_stats: TeamStats,
        league_means: dict[str, float],
        league_std_devs: dict[str, float],
        constant: float = 4.0,
    ) -> "TeamNerdStats":
        """
        Create TeamNerdStats from team statistics and league averages.

        This is the recommended way to create TeamNerdStats instances in production code.

        Args:
            team_stats: Individual team statistics
            league_means: Dictionary of league mean values for each stat
            league_std_devs: Dictionary of league standard deviations for each stat
            constant: Constant value (default 4.0)

        Returns:
            TeamNerdStats instance with calculated z-scores, adjustments, and components
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
        z_bullpen_runs = (
            team_stats.bullpen_runs - league_means["bullpen_runs"]
        ) / league_std_devs["bullpen_runs"]
        z_payroll = (team_stats.payroll - league_means["payroll"]) / league_std_devs[
            "payroll"
        ]
        z_age = (team_stats.age - league_means["age"]) / league_std_devs["age"]
        z_luck = (team_stats.luck - league_means["luck"]) / league_std_devs["luck"]
        z_broadcaster_rating = (
            team_stats.broadcaster_rating - league_means["broadcaster_rating"]
        ) / league_std_devs["broadcaster_rating"]
        z_radio_broadcaster_rating = (
            team_stats.radio_broadcaster_rating
            - league_means["radio_broadcaster_rating"]
        ) / league_std_devs["radio_broadcaster_rating"]

        # Apply caps and positive-only rules
        # For payroll, below average is better, so we want negative z_payroll values
        # We flip the sign and then apply positive-only rules
        adjusted_payroll = max(0.0, -z_payroll)
        # For age, younger is better, so we want negative z_age values (below mean age)
        # We flip the sign and then apply positive-only rules
        adjusted_age = max(0.0, -z_age)
        # For luck, apply positive-only rule and cap at 2.0
        adjusted_luck = max(0.0, min(2.0, z_luck))
        # For broadcaster rating, apply positive-only rule (higher is better)
        adjusted_broadcaster_rating = max(0.0, z_broadcaster_rating)
        # For radio broadcaster rating, apply positive-only rule (higher is better)
        adjusted_radio_broadcaster_rating = max(0.0, z_radio_broadcaster_rating)

        # Calculate individual components (stored to avoid duplication)
        batting_component = z_batting_runs
        barrel_component = z_barrel_rate
        baserunning_component = z_baserunning_runs
        fielding_component = z_fielding_runs
        bullpen_component = z_bullpen_runs
        payroll_component = adjusted_payroll
        age_component = adjusted_age
        luck_component = adjusted_luck
        broadcaster_component = adjusted_broadcaster_rating / 2.0
        radio_broadcaster_component = adjusted_radio_broadcaster_rating / 2.0
        constant_component = constant

        # Calculate tNERD score using the components
        tnerd_score = (
            batting_component
            + barrel_component
            + baserunning_component
            + fielding_component
            + bullpen_component
            + payroll_component
            + age_component
            + luck_component
            + broadcaster_component
            + radio_broadcaster_component
            + constant_component
        )

        return cls(
            team_stats=team_stats,
            z_batting_runs=z_batting_runs,
            z_barrel_rate=z_barrel_rate,
            z_baserunning_runs=z_baserunning_runs,
            z_fielding_runs=z_fielding_runs,
            z_bullpen_runs=z_bullpen_runs,
            z_payroll=z_payroll,
            z_age=z_age,
            z_luck=z_luck,
            z_broadcaster_rating=z_broadcaster_rating,
            z_radio_broadcaster_rating=z_radio_broadcaster_rating,
            adjusted_payroll=adjusted_payroll,
            adjusted_age=adjusted_age,
            adjusted_luck=adjusted_luck,
            adjusted_broadcaster_rating=adjusted_broadcaster_rating,
            adjusted_radio_broadcaster_rating=adjusted_radio_broadcaster_rating,
            batting_component=batting_component,
            barrel_component=barrel_component,
            baserunning_component=baserunning_component,
            fielding_component=fielding_component,
            bullpen_component=bullpen_component,
            payroll_component=payroll_component,
            age_component=age_component,
            luck_component=luck_component,
            broadcaster_component=broadcaster_component,
            radio_broadcaster_component=radio_broadcaster_component,
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
                bullpen_runs=raw_stats["Bullpen"],
                payroll=raw_stats["Payroll"],
                age=raw_stats["Payroll_Age"],
                luck=raw_stats["Luck"],
                broadcaster_rating=raw_stats["Broadcaster_Rating"],
                radio_broadcaster_rating=raw_stats["Radio_Broadcaster_Rating"],
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
    bullpen_runs = [team.bullpen_runs for team in all_teams]
    payrolls = [team.payroll for team in all_teams]
    ages = [team.age for team in all_teams]
    luck_values = [team.luck for team in all_teams]
    broadcaster_ratings = [team.broadcaster_rating for team in all_teams]
    radio_broadcaster_ratings = [team.radio_broadcaster_rating for team in all_teams]

    # Calculate means and standard deviations
    league_means = {
        "batting_runs": stats.tmean(batting_runs),
        "barrel_rate": stats.tmean(barrel_rates),
        "baserunning_runs": stats.tmean(baserunning_runs),
        "fielding_runs": stats.tmean(fielding_runs),
        "bullpen_runs": stats.tmean(bullpen_runs),
        "payroll": stats.tmean(payrolls),
        "age": stats.tmean(ages),
        "luck": stats.tmean(luck_values),
        "broadcaster_rating": stats.tmean(broadcaster_ratings),
        "radio_broadcaster_rating": stats.tmean(radio_broadcaster_ratings),
    }

    league_std_devs = {
        "batting_runs": stats.tstd(batting_runs),
        "barrel_rate": stats.tstd(barrel_rates),
        "baserunning_runs": stats.tstd(baserunning_runs),
        "fielding_runs": stats.tstd(fielding_runs),
        "bullpen_runs": stats.tstd(bullpen_runs),
        "payroll": stats.tstd(payrolls),
        "age": stats.tstd(ages),
        "luck": stats.tstd(luck_values),
        "broadcaster_rating": stats.tstd(broadcaster_ratings),
        "radio_broadcaster_rating": stats.tstd(radio_broadcaster_ratings),
    }

    # Calculate tNERD for each team
    team_nerd_details = {}
    for team_abbr, team_stats in team_stats_dict.items():
        try:
            team_nerd_stats = TeamNerdStats.from_stats_and_means(
                team_stats, league_means, league_std_devs
            )
            team_nerd_details[team_abbr] = team_nerd_stats
        except ValueError:
            # Skip teams with invalid tNERD scores (negative values)
            continue

    return team_nerd_details
