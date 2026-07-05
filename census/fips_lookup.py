"""
State FIPS code reference data, needed to scope county/ZIP-level Census
ACS queries to a specific state (the API requires &in=state:XX for
sub-state geographies).

Source: U.S. Census Bureau standard state FIPS codes (public reference data).
"""

STATE_FIPS = {
    "Alabama": "01", "Alaska": "02", "Arizona": "04", "Arkansas": "05",
    "California": "06", "Colorado": "08", "Connecticut": "09", "Delaware": "10",
    "District of Columbia": "11", "Florida": "12", "Georgia": "13", "Hawaii": "15",
    "Idaho": "16", "Illinois": "17", "Indiana": "18", "Iowa": "19",
    "Kansas": "20", "Kentucky": "21", "Louisiana": "22", "Maine": "23",
    "Maryland": "24", "Massachusetts": "25", "Michigan": "26", "Minnesota": "27",
    "Mississippi": "28", "Missouri": "29", "Montana": "30", "Nebraska": "31",
    "Nevada": "32", "New Hampshire": "33", "New Jersey": "34", "New Mexico": "35",
    "New York": "36", "North Carolina": "37", "North Dakota": "38", "Ohio": "39",
    "Oklahoma": "40", "Oregon": "41", "Pennsylvania": "42", "Rhode Island": "44",
    "South Carolina": "45", "South Dakota": "46", "Tennessee": "47", "Texas": "48",
    "Utah": "49", "Vermont": "50", "Virginia": "51", "Washington": "53",
    "West Virginia": "54", "Wisconsin": "55", "Wyoming": "56", "Puerto Rico": "72",
}

STATE_ABBREV_TO_NAME = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming", "PR": "Puerto Rico",
}


def get_state_fips(state_identifier: str) -> str:
    """
    Get a state's FIPS code from either its full name ('Florida') or
    2-letter abbreviation ('FL'). Case-insensitive on full names.
    """
    if state_identifier in STATE_ABBREV_TO_NAME:
        state_identifier = STATE_ABBREV_TO_NAME[state_identifier]

    for name, fips in STATE_FIPS.items():
        if name.lower() == state_identifier.lower():
            return fips

    raise ValueError(f"Unknown state identifier: {state_identifier}")

# ZIP code prefix (first 3 digits) ranges per state. Used because the Census
# API's ZCTA (ZIP Code Tabulation Area) geography does NOT support &in=state:XX
# filtering - ZCTAs don't nest cleanly within states (some straddle state
# lines), so &for=zip code tabulation area:*&in=state:XX returns a 400 error.
# This is a documented API limitation (see census.gov ZCTA geography notes and
# the censusapi R package issue tracker). The standard workaround is to pull
# ZCTA data nationally and filter by known ZIP prefix ranges per state.
STATE_ZIP_PREFIX_RANGES = {
    "Florida": [(320, 349)],
    "California": [(900, 961)],
    "New York": [(100, 149)],
    "Texas": [(750, 799), (885, 885)],
    "Georgia": [(300, 319), (398, 399)],
    "Alabama": [(350, 369)],
    # Add more states as needed - this is intentionally not exhaustive;
    # extend the table for whichever states the pipeline actually targets.
}


def get_zip_prefixes_for_state(state: str) -> list:
    """Return the list of (start, end) 3-digit ZIP prefix ranges for a state."""
    resolved_name = STATE_ABBREV_TO_NAME.get(state, state)
    for name, ranges in STATE_ZIP_PREFIX_RANGES.items():
        if name.lower() == resolved_name.lower():
            return ranges
    raise ValueError(
        f"No ZIP prefix range defined for '{state}'. "
        f"Add it to STATE_ZIP_PREFIX_RANGES in fips_lookup.py."
    )