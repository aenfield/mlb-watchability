"""Pitcher statistics data structures for pNERD calculation."""

from dataclasses import dataclass

from scipy import stats  # type: ignore

from .data_retrieval import get_all_pitcher_stats

# we skip ruff linting for magic values a bunch of places below with noqa for PLR2004, since it's
# clearer and less verbose and we don't need to use these checks in other places


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

        # Adjusted values validation
        if not 0.0 <= self.adjusted_velocity <= 2.0:  # noqa: PLR2004
            raise ValueError(
                f"Adjusted velocity must be between 0.0 and 2.0, got {self.adjusted_velocity}"
            )

        if not 0.0 <= self.adjusted_age <= 2.0:  # noqa: PLR2004
            raise ValueError(
                f"Adjusted age must be between 0.0 and 2.0, got {self.adjusted_age}"
            )

        if not 0.0 <= self.adjusted_luck <= 1.0:  # noqa: PLR2004
            raise ValueError(
                f"Adjusted luck must be between 0.0 and 1.0, got {self.adjusted_luck}"
            )

        # pNERD score should be positive (typically 0-20)
        if not 0.0 <= self.pnerd_score <= 50.0:  # noqa: PLR2004
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

    Formula: (zxFIP- * 2) + (zSwStrk / 2) + (zStrk / 2) + zVelo + zAge + (-zPace / 2) + (Luck / 20) + (KN * 5) + Constant

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
    adjusted_velocity = max(0.0, min(2.0, z_velocity))  # noqa: PLR2004
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
        + (-z_pace / 2)
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


def get_all_pitcher_stats_objects(season: int = 2025) -> dict[str, PitcherStats]:
    """
    Get all pitcher statistics as PitcherStats objects.

    Args:
        season: Season year (default: 2025)

    Returns:
        Dictionary mapping pitcher names to PitcherStats objects

    Raises:
        RuntimeError: If data retrieval fails
    """
    try:
        # Get raw pitcher data
        raw_pitcher_data = get_all_pitcher_stats(season)

        # Create PitcherStats objects from raw data
        pitcher_stats_dict = {}
        for name, raw_stats in raw_pitcher_data.items():
            pitcher_stats = PitcherStats(
                name=raw_stats["Name"],
                team=raw_stats["Team"],
                xfip_minus=raw_stats["xFIP-"],
                swinging_strike_rate=raw_stats["SwStr%"],
                strike_rate=raw_stats["Strike_Rate"],
                velocity=raw_stats["FBv"],
                age=raw_stats["Age"],
                pace=raw_stats["Pace"],
                luck=raw_stats["Luck"],
                knuckleball_rate=raw_stats["KN%"],
            )
            pitcher_stats_dict[name] = pitcher_stats

    except Exception as e:
        raise RuntimeError(
            f"Failed to create pitcher stats objects for season {season}: {str(e)}"
        ) from e
    else:
        return pitcher_stats_dict


def calculate_pitcher_nerd_scores(season: int = 2025) -> dict[str, float]:
    """Calculate pitcher NERD scores for all pitchers."""
    detailed_stats = calculate_detailed_pitcher_nerd_scores(season)
    return {
        pitcher: nerd_stats.pnerd_score
        for pitcher, nerd_stats in detailed_stats.items()
    }


def calculate_detailed_pitcher_nerd_scores(
    season: int = 2025,
) -> dict[str, PitcherNerdStats]:
    """Calculate detailed pitcher NERD scores for all pitchers."""
    try:
        # Get all pitcher stats
        pitcher_stats_dict = get_all_pitcher_stats_objects(season)

        # Calculate league means and standard deviations
        all_pitchers = list(pitcher_stats_dict.values())

        # Extract values for each stat
        xfip_minus_values = [pitcher.xfip_minus for pitcher in all_pitchers]
        swinging_strike_rates = [
            pitcher.swinging_strike_rate for pitcher in all_pitchers
        ]
        strike_rates = [pitcher.strike_rate for pitcher in all_pitchers]
        velocities = [pitcher.velocity for pitcher in all_pitchers]
        ages = [pitcher.age for pitcher in all_pitchers]
        paces = [pitcher.pace for pitcher in all_pitchers]

        # Calculate means and standard deviations
        league_means = {
            "xfip_minus": stats.tmean(xfip_minus_values),
            "swinging_strike_rate": stats.tmean(swinging_strike_rates),
            "strike_rate": stats.tmean(strike_rates),
            "velocity": stats.tmean(velocities),
            "age": stats.tmean(ages),
            "pace": stats.tmean(paces),
        }

        league_std_devs = {
            "xfip_minus": stats.tstd(xfip_minus_values),
            "swinging_strike_rate": stats.tstd(swinging_strike_rates),
            "strike_rate": stats.tstd(strike_rates),
            "velocity": stats.tstd(velocities),
            "age": stats.tstd(ages),
            "pace": stats.tstd(paces),
        }

        # Calculate pNERD for each pitcher
        pitcher_nerd_details = {}
        for pitcher_name, pitcher_stats in pitcher_stats_dict.items():
            try:
                pitcher_nerd_stats = calculate_pnerd_score(
                    pitcher_stats, league_means, league_std_devs
                )
                pitcher_nerd_details[pitcher_name] = pitcher_nerd_stats
            except ValueError:
                # Skip pitchers with invalid pNERD scores (negative values)
                continue

    except Exception:
        # If calculation fails, return empty dict
        return {}
    else:
        return pitcher_nerd_details
