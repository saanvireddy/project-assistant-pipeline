import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

from feature_engineering import (
    add_income_ratios,
    add_population_buckets,
    add_income_percentile_rank,
    add_match_confidence_tier,
    engineer_census_features,
    engineer_country_features,
)


def test_income_ratio_calculation():
    df = pd.DataFrame({
        "per_capita_income": [32000],
        "median_household_income": [55000],
    })
    result = add_income_ratios(df)
    assert abs(result["income_ratio_percapita_to_household"].iloc[0] - (32000 / 55000)) < 1e-6


def test_income_ratio_handles_missing_columns_gracefully():
    df = pd.DataFrame({"total_population": [1000]})
    result = add_income_ratios(df)
    assert "income_ratio_percapita_to_household" not in result.columns


def test_population_buckets():
    df = pd.DataFrame({"total_population": [5000, 30000, 100000, 500000, 2000000]})
    result = add_population_buckets(df)
    expected = ["very_small", "small", "medium", "large", "very_large"]
    assert result["total_population_bucket"].tolist() == expected


def test_income_percentile_rank():
    df = pd.DataFrame({"median_household_income": [30000, 60000, 90000]})
    result = add_income_percentile_rank(df)
    assert result["median_household_income_percentile"].iloc[2] == 100.0
    assert result["median_household_income_percentile"].iloc[0] < result["median_household_income_percentile"].iloc[1]


def test_match_confidence_tiers():
    df = pd.DataFrame({"confidence": [100, 85, 65, 0, np.nan]})
    result = add_match_confidence_tier(df)
    assert result["match_confidence_tier"].tolist() == ["high", "medium", "low", "none", "none"]


def test_engineer_census_features_end_to_end():
    df = pd.DataFrame({
        "total_population": [8000, 2700000],
        "median_household_income": [42000, 55000],
        "per_capita_income": [21000, 32000],
    })
    result = engineer_census_features(df)
    assert "income_ratio_percapita_to_household" in result.columns
    assert "total_population_bucket" in result.columns
    assert "median_household_income_percentile" in result.columns


def test_engineer_country_features_end_to_end():
    df = pd.DataFrame({"confidence": [100, 60]})
    result = engineer_country_features(df)
    assert "match_confidence_tier" in result.columns