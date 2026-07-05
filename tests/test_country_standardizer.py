import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etl"))

from country_standardizer import standardize_country


def test_alias_override():
    result = standardize_country("USA")
    assert result["canonical_name"] == "United States of America"
    assert result["iso3"] == "USA"
    assert result["match_method"] == "alias_override"


def test_historical_successor():
    result = standardize_country("USSR")
    assert result["canonical_name"] == "Russian Federation"
    assert result["match_method"] == "historical_successor_override"


def test_non_standardizable_not_forced():
    result = standardize_country("European Union")
    assert result["canonical_name"] is None
    assert result["match_method"] == "non_standardizable_entity"


def test_exact_match():
    result = standardize_country("Germany")
    assert result["iso3"] == "DEU"
    assert result["match_method"] == "exact_match"


def test_fuzzy_match_typo():
    result = standardize_country("Untied States")  # typo
    assert result["canonical_name"] == "United States of America"
    assert result["match_method"] == "fuzzy_match"


def test_empty_input():
    result = standardize_country("")
    assert result["canonical_name"] is None
    assert result["match_method"] == "empty_input"


def test_unmatched_low_confidence():
    result = standardize_country("Xyzland Nowhere Made Up Place")
    assert result["canonical_name"] is None
    assert result["match_method"] == "unmatched"