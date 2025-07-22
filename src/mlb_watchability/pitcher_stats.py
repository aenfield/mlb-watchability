"""Pitcher statistics data structures for pNERD calculation."""

import unicodedata
from dataclasses import dataclass

import pandas as pd
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

    # Component values
    xfip_component: float = 0.0
    swinging_strike_component: float = 0.0
    strike_component: float = 0.0
    velocity_component: float = 0.0
    age_component: float = 0.0
    pace_component: float = 0.0
    luck_component: float = 0.0
    knuckleball_component: float = 0.0
    constant_component: float = 0.0

    @classmethod
    def from_stats_and_means(
        cls,
        pitcher_stats: PitcherStats,
        league_means: dict[str, float],
        league_std_devs: dict[str, float],
    ) -> "PitcherNerdStats":
        """
        Create PitcherNerdStats from pitcher statistics and league averages.

        This is the recommended way to create PitcherNerdStats instances in production code.

        Args:
            pitcher_stats: Individual pitcher statistics
            league_means: Dictionary of league mean values for each stat
            league_std_devs: Dictionary of league standard deviations for each stat

        Returns:
            PitcherNerdStats instance with calculated z-scores, adjustments, and components
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

        z_velocity = (
            pitcher_stats.velocity - league_means["velocity"]
        ) / league_std_devs["velocity"]

        z_age = (pitcher_stats.age - league_means["age"]) / league_std_devs["age"]

        z_pace = (pitcher_stats.pace - league_means["pace"]) / league_std_devs["pace"]

        # Apply caps and adjustments
        adjusted_velocity = max(0.0, min(2.0, z_velocity))
        adjusted_age = max(0.0, min(2.0, -z_age))  # Negative because younger is better
        adjusted_luck = max(
            0.0, min(1.0, pitcher_stats.luck)
        )  # Cap directly without negating

        # Calculate individual components
        xfip_component = -z_xfip_minus * 2  # Negated because lower xFIP- is better
        swinging_strike_component = z_swinging_strike_rate / 2
        strike_component = z_strike_rate / 2
        velocity_component = adjusted_velocity
        age_component = adjusted_age
        pace_component = -z_pace / 2  # Negated because lower pace (faster) is better
        luck_component = adjusted_luck / 20
        knuckleball_component = pitcher_stats.knuckleball_rate * 5.0
        constant_component = 3.8

        # Calculate final pNERD score using the components
        pnerd_score = (
            xfip_component
            + swinging_strike_component
            + strike_component
            + velocity_component
            + age_component
            + pace_component
            + luck_component
            + knuckleball_component
            + constant_component
        )

        return cls(
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
            xfip_component=xfip_component,
            swinging_strike_component=swinging_strike_component,
            strike_component=strike_component,
            velocity_component=velocity_component,
            age_component=age_component,
            pace_component=pace_component,
            luck_component=luck_component,
            knuckleball_component=knuckleball_component,
            constant_component=constant_component,
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
                pitcher_nerd_stats = PitcherNerdStats.from_stats_and_means(
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


def remove_accented_characters(name: str) -> str:
    """
    Remove all accented characters from a pitcher name.

    Args:
        name: Pitcher name with potential accented characters (e.g. "Jesús Luzardo")

    Returns:
        Name with accented characters removed (e.g. "Jesus Luzardo")
    """
    if not name:
        return name

    # Normalize unicode to decomposed form (NFD) then remove combining characters
    normalized = unicodedata.normalize("NFD", name)
    # Filter out combining characters (accents, diacritics)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def map_mlbam_name_to_fangraphs_name(mlbam_name: str) -> str:
    """
    Map MLBAM pitcher name to Fangraphs name using data/name-mapping.csv.

    Args:
        mlbam_name: Pitcher name as it appears in MLBAM/schedule data

    Returns:
        Fangraphs name if mapping exists, otherwise returns the original mlbam_name

    Raises:
        FileNotFoundError: If name-mapping.csv file doesn't exist
        OSError: If file can't be read
        KeyError: If CSV doesn't have expected columns
    """
    if not mlbam_name:
        return mlbam_name

    # Get path to name mapping CSV file - use pandas like other CSV files in the codebase
    csv_path = "data/name-mapping.csv"

    # try:
    mapping_df = pd.read_csv(csv_path)
    # Look for matching mlbam_name
    matches = mapping_df[mapping_df["mlbam_name"] == mlbam_name]
    if not matches.empty:
        return str(matches.iloc[0]["fangraphs_name"])
    # except FileNotFoundError as err:
    #     raise FileNotFoundError(f"Name mapping file not found: {csv_path}") from err
    else:
        # If no mapping found, return original name
        return mlbam_name


def find_pitcher_nerd_stats_fuzzy(
    pitcher_nerd_stats: dict[str, PitcherNerdStats], pitcher_name: str
) -> PitcherNerdStats | None:
    """
    Find pitcher NERD stats using fuzzy matching techniques.

    Attempts multiple lookup strategies in order:
    1. Direct lookup with unmodified pitcher_name
    2. Lookup with accented characters removed
    3. Lookup using MLBAM to Fangraphs name mapping

    Args:
        pitcher_nerd_stats: Dictionary mapping pitcher names to PitcherNerdStats
        pitcher_name: Pitcher name to search for

    Returns:
        PitcherNerdStats if found, otherwise None
    """
    if not pitcher_name or pitcher_name == "TBD":
        return None

    # Strategy 1: Try direct lookup
    if pitcher_name in pitcher_nerd_stats:
        return pitcher_nerd_stats[pitcher_name]

    # Strategy 2: Try with accented characters removed
    try:
        name_no_accents = remove_accented_characters(pitcher_name)
        if name_no_accents != pitcher_name and name_no_accents in pitcher_nerd_stats:
            return pitcher_nerd_stats[name_no_accents]
    except Exception:
        # If accent removal fails, continue to next strategy
        pass

    # Strategy 3: Try MLBAM to Fangraphs mapping
    try:
        fangraphs_name = map_mlbam_name_to_fangraphs_name(pitcher_name)
        if fangraphs_name != pitcher_name and fangraphs_name in pitcher_nerd_stats:
            return pitcher_nerd_stats[fangraphs_name]
    except Exception:
        # If mapping fails (file not found, etc.), continue
        pass

    # All strategies failed
    return None


def format_pitcher_with_fangraphs_link(pitcher_name: str) -> str:
    """Format pitcher name as a markdown link to Fangraphs player search page."""
    if not pitcher_name or pitcher_name == "TBD":
        return "TBD"

    # Extract last name for search
    name_parts = pitcher_name.split()
    last_name = name_parts[-1] if name_parts else pitcher_name

    # Fangraphs search URL format: https://www.fangraphs.com/search?q={last_name}
    fangraphs_url = f"https://www.fangraphs.com/search?q={last_name}"

    return f"[{pitcher_name}]({fangraphs_url})"
