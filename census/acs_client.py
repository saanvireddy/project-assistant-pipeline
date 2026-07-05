"""
Client for the U.S. Census Bureau ACS 5-Year Data API.

Supports state, county, and ZCTA (ZIP Code Tabulation Area) level queries
using FIPS-based conditional logic: county/ZIP-level queries must be scoped
to a state via &in=state:XX, while state-level queries use &for=state:*.

Requires CENSUS_API_KEY set in environment (.env file, via python-dotenv).
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv

from fips_lookup import get_state_fips

load_dotenv()

BASE_URL = "https://api.census.gov/data"

DEFAULT_VARIABLES = {
    "B01003_001E": "total_population",
    "B19013_001E": "median_household_income",
    "B19301_001E": "per_capita_income",
}


def _get_api_key() -> str:
    api_key = os.getenv("CENSUS_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "CENSUS_API_KEY not found. Set it in a .env file or environment variable."
        )
    return api_key


def _build_request(year: int, variables: list, for_geo: str, in_geo: str = None) -> tuple:
    """
    Build the request URL and params separately, letting `requests` handle
    proper URL encoding (e.g. spaces in "zip code tabulation area:*" must be
    percent-encoded - manual string concatenation would send an invalid URL).
    """
    var_string = ",".join(["NAME"] + variables)
    url = f"{BASE_URL}/{year}/acs/acs5"
    params = {"get": var_string, "for": for_geo, "key": _get_api_key()}
    if in_geo:
        params["in"] = in_geo
    return url, params


def _fetch(url: str, params: dict) -> list:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _rows_to_dataframe(raw_json: list, variables: list) -> pd.DataFrame:
    """
    Census API returns [[header_row], [data_row1], [data_row2], ...].
    Convert to a proper dataframe and rename variable codes to readable names.
    """
    header, *rows = raw_json
    df = pd.DataFrame(rows, columns=header)

    rename_map = {code: name for code, name in DEFAULT_VARIABLES.items() if code in variables}
    df = df.rename(columns=rename_map)

    for col in rename_map.values():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def get_state_level_data(year: int = 2022, variables: list = None) -> pd.DataFrame:
    """Pull demographic/income data for all 50 states + DC."""
    variables = variables or list(DEFAULT_VARIABLES.keys())
    url, params = _build_request(year, variables, for_geo="state:*")
    raw = _fetch(url, params)
    return _rows_to_dataframe(raw, variables)


def get_county_level_data(state: str, year: int = 2022, variables: list = None) -> pd.DataFrame:
    """
    Pull demographic/income data for all counties within a given state.
    state: full name ('Florida') or abbreviation ('FL').
    """
    variables = variables or list(DEFAULT_VARIABLES.keys())
    state_fips = get_state_fips(state)
    url, params = _build_request(year, variables, for_geo="county:*", in_geo=f"state:{state_fips}")
    raw = _fetch(url, params)
    return _rows_to_dataframe(raw, variables)

def get_zip_level_data(state: str, year: int = 2022, variables: list = None) -> pd.DataFrame:
    """
    Pull demographic/income data for ZCTAs (ZIP Code Tabulation Areas) within
    a given state.

    Note: the Census API does NOT support &in=state:XX for ZCTA geography
    (ZCTAs can straddle state lines, so they aren't scoped under states in
    the API's geographic hierarchy - a state-scoped ZCTA query returns a 400
    error). This pulls ZCTA data nationally, then filters to the target
    state using known ZIP code prefix ranges.
    """
    from fips_lookup import get_zip_prefixes_for_state

    variables = variables or list(DEFAULT_VARIABLES.keys())
    url, params = _build_request(year, variables, for_geo="zip code tabulation area:*")
    raw = _fetch(url, params)
    df = _rows_to_dataframe(raw, variables)

    zcta_col = "zip code tabulation area"
    prefix_ranges = get_zip_prefixes_for_state(state)

    def _in_state(zcta: str) -> bool:
        try:
            prefix = int(str(zcta)[:3])
        except (ValueError, TypeError):
            return False
        return any(low <= prefix <= high for low, high in prefix_ranges)

    return df[df[zcta_col].apply(_in_state)].reset_index(drop=True)