"""Centralized team name and abbreviation mappings for MLB Watchability."""

# Standard team name to abbreviation mapping
# Maps full team names (as used in game schedules) to standard MLB abbreviations
TEAM_NAME_TO_ABBREVIATION = {
    "Arizona Diamondbacks": "ARI",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CHW",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KCR",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Mets": "NYM",
    "New York Yankees": "NYY",
    "Oakland Athletics": "ATH",
    "Athletics": "ATH",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SDP",
    "San Francisco Giants": "SFG",
    "Seattle Mariners": "SEA",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TBR",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSN",
}

# Payroll data abbreviation mapping
# Maps team abbreviations used in payroll CSV to standard MLB abbreviations
PAYROLL_TO_STANDARD_ABBREVIATION = {
    "TB": "TBR",
    "WSH": "WSN",
    "SD": "SDP",
    "SF": "SFG",
    "KC": "KCR",
}

# Fangraphs team URL mappings
# Maps standard team abbreviations to Fangraphs URL slugs
TEAM_ABBREVIATION_TO_FANGRAPHS = {
    "ARI": "diamondbacks",
    "ATL": "braves",
    "BAL": "orioles",
    "BOS": "red-sox",
    "CHC": "cubs",
    "CHW": "white-sox",
    "CIN": "reds",
    "CLE": "guardians",
    "COL": "rockies",
    "DET": "tigers",
    "HOU": "astros",
    "KCR": "royals",
    "LAA": "angels",
    "LAD": "dodgers",
    "MIA": "marlins",
    "MIL": "brewers",
    "MIN": "twins",
    "NYM": "mets",
    "NYY": "yankees",
    "ATH": "athletics",
    "PHI": "phillies",
    "PIT": "pirates",
    "SDP": "padres",
    "SFG": "giants",
    "SEA": "mariners",
    "STL": "cardinals",
    "TBR": "rays",
    "TEX": "rangers",
    "TOR": "blue-jays",
    "WSN": "nationals",
}


def get_team_abbreviation(full_name: str) -> str:
    """
    Convert full team name to standard abbreviation.

    Args:
        full_name: Full team name (e.g., "Arizona Diamondbacks")

    Returns:
        Standard team abbreviation (e.g., "ARI"), or the input if not found
    """
    return TEAM_NAME_TO_ABBREVIATION.get(full_name, full_name)


def normalize_payroll_team_abbreviation(payroll_abbr: str) -> str:
    """
    Convert payroll data team abbreviation to standard abbreviation.

    Args:
        payroll_abbr: Team abbreviation from payroll data (e.g., "TB")

    Returns:
        Standard team abbreviation (e.g., "TBR"), or the input if not found
    """
    return PAYROLL_TO_STANDARD_ABBREVIATION.get(payroll_abbr, payroll_abbr)


def get_fangraphs_team_slug(team_name: str) -> str:
    """
    Get Fangraphs URL slug for a team.

    Args:
        team_name: Full team name (e.g., "Boston Red Sox")

    Returns:
        Fangraphs team slug (e.g., "red-sox"), or team abbreviation if not found
    """
    team_abbr = get_team_abbreviation(team_name)
    return TEAM_ABBREVIATION_TO_FANGRAPHS.get(team_abbr, team_abbr.lower())


def format_team_with_fangraphs_link(team_name: str) -> str:
    """Format team name as a markdown link to Fangraphs team page."""
    if not team_name:
        return "TBD"

    # Get Fangraphs team slug for URL
    team_slug = get_fangraphs_team_slug(team_name)

    # Fangraphs team URL format: https://www.fangraphs.com/teams/{team_slug}/stats
    fangraphs_url = f"https://www.fangraphs.com/teams/{team_slug}/stats"

    return f"[{team_name}]({fangraphs_url})"
