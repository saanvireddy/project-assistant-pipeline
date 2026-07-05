"""
Canonical ISO 3166-1 country reference data.

Source: lukes/ISO-3166-Countries-with-Regional-Codes (MIT licensed, public dataset
built from ISO 3166-1 / UN M49 data). https://github.com/lukes/ISO-3166-Countries-with-Regional-Codes
Loaded from data/raw/iso_3166_full_reference.csv - 249 countries/territories,
real ISO alpha-2 and alpha-3 codes.
"""

import os
import pandas as pd

_REFERENCE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "raw", "iso_3166_full_reference.csv"
)


def _load_iso_countries():
    df = pd.read_csv(_REFERENCE_PATH)
    return [
        {"name": row["name"], "iso2": row["alpha-2"], "iso3": row["alpha-3"]}
        for _, row in df.iterrows()
    ]


ISO_COUNTRIES = _load_iso_countries()