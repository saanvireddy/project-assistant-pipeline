"""
Ties the ACS client together into an analytics-ready output: pulls state,
county, and ZIP-level demographic/income data for a given state and saves
to data/processed/ for downstream use in Tableau, ML pipelines, and the
RAG pipeline.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

import pandas as pd
from acs_client import get_state_level_data, get_county_level_data, get_zip_level_data
from schema_validator import build_schema_report
from quality_checks import run_quality_report

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

ACS_SCHEMA = {
    "NAME": {"dtype": "object", "required": True},
    "total_population": {"dtype": "float64", "required": True},
    "median_household_income": {"dtype": "float64", "required": False},
}


def build_census_datasets(state: str, year: int = 2022) -> dict:
    """
    Pull state, county, and ZIP-level data for a given state, validate and
    quality-check each, and save to data/processed/.
    """
    datasets = {
        "state": get_state_level_data(year=year),
        "county": get_county_level_data(state=state, year=year),
        "zip": get_zip_level_data(state=state, year=year),
    }

    for level, df in datasets.items():
        schema_report = build_schema_report(df, ACS_SCHEMA, strict_types=False)
        quality_report = run_quality_report(
            df,
            missing_check_columns=["total_population"],
            range_checks={"total_population": {"min_val": 0}},
        )
        print(f"[{level}] schema passed: {schema_report['passed']}, quality passed: {quality_report['passed']}")

        out_path = os.path.join(OUTPUT_DIR, f"acs_{level}_{state.lower()}_{year}.csv")
        df.to_csv(out_path, index=False)
        print(f"[{level}] saved {len(df)} rows to {out_path}")

    return datasets


if __name__ == "__main__":
    build_census_datasets(state="Florida", year=2022)