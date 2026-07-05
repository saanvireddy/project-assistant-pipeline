"""
Tests for the Census ACS client. Live API calls are excluded from automated
tests (require a real CENSUS_API_KEY + network) - those are verified
manually with: python census/pipeline.py
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "census"))

from fips_lookup import get_state_fips
from acs_client import _build_request, _rows_to_dataframe


def test_fips_lookup_full_name():
    assert get_state_fips("Florida") == "12"


def test_fips_lookup_abbreviation():
    assert get_state_fips("FL") == "12"


def test_fips_lookup_case_insensitive():
    assert get_state_fips("california") == "06"


def test_fips_lookup_unknown_state_raises():
    with pytest.raises(ValueError):
        get_state_fips("Narnia")


def test_build_request_state_level(monkeypatch):
    monkeypatch.setenv("CENSUS_API_KEY", "test_key")
    url, params = _build_request(2022, ["B01003_001E"], for_geo="state:*")
    assert params["for"] == "state:*"
    assert params["key"] == "test_key"
    assert "in" not in params


def test_build_request_county_level_includes_state_filter(monkeypatch):
    monkeypatch.setenv("CENSUS_API_KEY", "test_key")
    url, params = _build_request(2022, ["B01003_001E"], for_geo="county:*", in_geo="state:12")
    assert params["in"] == "state:12"


def test_build_request_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("CENSUS_API_KEY", raising=False)
    with pytest.raises(EnvironmentError):
        _build_request(2022, ["B01003_001E"], for_geo="state:*")


def test_rows_to_dataframe_parses_and_renames():
    mock_response = [
        ["NAME", "B01003_001E", "B19013_001E", "state"],
        ["Florida", "21781128", "61777", "12"],
    ]
    df = _rows_to_dataframe(mock_response, ["B01003_001E", "B19013_001E"])
    assert "total_population" in df.columns
    assert "median_household_income" in df.columns
    assert df["total_population"].iloc[0] == 21781128
    assert df["total_population"].dtype.kind in ("i", "f")