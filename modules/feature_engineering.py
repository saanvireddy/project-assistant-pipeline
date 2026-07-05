"""
Feature engineering utilities: derive model-ready features from cleaned
Census/demographic data and standardized country records.

These are the transformations that turn "clean data" into "features a model
or dashboard can actually use" - ratios, buckets/categories, and normalized
scores, rather than raw estimates.
"""

import pandas as pd
import numpy as np


def add_income_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive per-capita-to-median-household income ratio - a simple signal of
    income concentration/inequality within a geography (a ratio well above 1
    suggests smaller households or higher earners; well below suggests larger
    households relative to income).
    """
    df = df.copy()
    if "per_capita_income" in df.columns and "median_household_income" in df.columns:
        df["income_ratio_percapita_to_household"] = (
            df["per_capita_income"] / df["median_household_income"]
        ).replace([np.inf, -np.inf], np.nan)
    return df


def add_population_buckets(df: pd.DataFrame, column: str = "total_population") -> pd.DataFrame:
    """
    Bucket population into categorical size bands. Useful for downstream
    grouping/BI (e.g. Tableau filters) without re-deriving thresholds
    every time, and for models that benefit from a categorical alongside
    the continuous value.
    """
    df = df.copy()
    if column not in df.columns:
        return df

    bins = [0, 10_000, 50_000, 200_000, 1_000_000, np.inf]
    labels = ["very_small", "small", "medium", "large", "very_large"]
    df[f"{column}_bucket"] = pd.cut(df[column], bins=bins, labels=labels, right=False)
    return df


def add_income_percentile_rank(df: pd.DataFrame, column: str = "median_household_income") -> pd.DataFrame:
    """
    Add a 0-100 percentile rank for a numeric column within the given
    dataframe (e.g. how a county's income ranks among all counties in the
    same pull). More interpretable across a dataset than the raw dollar
    figure alone, and normalizes across pulls of different geographic scope.
    """
    df = df.copy()
    if column in df.columns:
        df[f"{column}_percentile"] = df[column].rank(pct=True) * 100
    return df


def add_match_confidence_tier(df: pd.DataFrame, confidence_col: str = "confidence") -> pd.DataFrame:
    """
    Bucket ETL match confidence scores into tiers (high/medium/low/none) -
    a categorical feature useful for filtering which standardized records
    are safe to trust downstream without manual review.
    """
    df = df.copy()
    if confidence_col not in df.columns:
        return df

    def _tier(score):
        if pd.isna(score) or score == 0:
            return "none"
        if score >= 95:
            return "high"
        if score >= 80:
            return "medium"
        return "low"

    df["match_confidence_tier"] = df[confidence_col].apply(_tier)
    return df


def engineer_census_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the full census feature engineering suite in one call."""
    df = add_income_ratios(df)
    df = add_population_buckets(df)
    df = add_income_percentile_rank(df)
    return df


def engineer_country_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the full country/ETL feature engineering suite in one call."""
    df = add_match_confidence_tier(df)
    return df