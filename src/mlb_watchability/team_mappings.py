"""Centralized team name and abbreviation mappings for MLB Watchability."""

# Standard team name to abbreviation mapping
# Maps full team names (as used in game schedules) to standard MLB abbreviations
TEAM_NAME_TO_ABBREVIATION = {
    "Arizona Diamondbacks": "ARI",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CWS",
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
    "Oakland Athletics": "OAK",
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
