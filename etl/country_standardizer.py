"""
ETL: Country Name -> ISO Code Standardization

Pipeline order (deliberate, in this priority):
1. Exact alias override (fast, 100% precision for known cases)
2. Historical successor override (explicit, auditable assumption)
3. Non-standardizable flag (supranational entities - do not force-match)
4. RapidFuzz fuzzy match against canonical ISO country list (catch-all)

Anything below the confidence threshold is logged as unmatched rather than
silently assigned a wrong ISO code - this is what protects the ~90% figure
from becoming a false precision claim.
"""

import pandas as pd
from rapidfuzz import process, fuzz

from iso_reference import ISO_COUNTRIES
from etl.country_overrides import ALIAS_OVERRIDES, HISTORICAL_SUCCESSOR_OVERRIDES, NON_STANDARDIZABLE

FUZZY_MATCH_THRESHOLD = 60  # below this, flag for manual review instead of guessing
# token_sort_ratio chosen over WRatio: WRatio's length-weighting caused mismatches
# against the full 249-country list (e.g. "Untied States" typo matched
# "Micronesia, Federated States of" instead of "United States of America").
# token_sort_ratio compares word sets directly, which is more robust here.
_FUZZY_SCORER = fuzz.token_sort_ratio

_NAME_TO_ISO = {c["name"]: c for c in ISO_COUNTRIES}
_CANONICAL_NAMES = list(_NAME_TO_ISO.keys())


def standardize_country(raw_name: str) -> dict:
    """
    Standardize a single raw country name string into ISO codes.
    Returns a dict with the match, method used, and confidence.
    """
    if not isinstance(raw_name, str) or not raw_name.strip():
        return _build_result(raw_name, None, "empty_input", 0)

    cleaned = raw_name.strip()
    key = cleaned.lower()

    # 1. Exact alias override
    if key in ALIAS_OVERRIDES:
        canonical = ALIAS_OVERRIDES[key]
        return _build_result(raw_name, canonical, "alias_override", 100)

    # 2. Historical successor override
    if key in HISTORICAL_SUCCESSOR_OVERRIDES:
        canonical = HISTORICAL_SUCCESSOR_OVERRIDES[key]
        return _build_result(raw_name, canonical, "historical_successor_override", 100)

    # 3. Non-standardizable entities
    if key in NON_STANDARDIZABLE:
        return _build_result(raw_name, None, "non_standardizable_entity", 0)

    # 4. Exact match against canonical names (case-insensitive)
    for name in _CANONICAL_NAMES:
        if name.lower() == key:
            return _build_result(raw_name, name, "exact_match", 100)

    # 5. Fuzzy match fallback
    match, score, _ = process.extractOne(
        cleaned, _CANONICAL_NAMES, scorer=_FUZZY_SCORER
    )
    if score >= FUZZY_MATCH_THRESHOLD:
        return _build_result(raw_name, match, "fuzzy_match", score)

    return _build_result(raw_name, None, "unmatched", score)


def _build_result(raw_name, canonical_name, method, confidence):
    iso_info = _NAME_TO_ISO.get(canonical_name, {})
    return {
        "raw_name": raw_name,
        "canonical_name": canonical_name,
        "iso2": iso_info.get("iso2"),
        "iso3": iso_info.get("iso3"),
        "match_method": method,
        "confidence": confidence,
    }


def standardize_dataframe(df: pd.DataFrame, country_col: str = "country_name") -> pd.DataFrame:
    """
    Apply standardization to an entire dataframe column and merge results in.
    """
    results = df[country_col].apply(standardize_country).apply(pd.Series)
    return pd.concat([df.reset_index(drop=True), results], axis=1)


def run_report(df: pd.DataFrame) -> None:
    """Print a mismatch-reduction summary, the actual metric behind the resume bullet."""
    total = len(df)
    unmatched = (df["match_method"] == "unmatched").sum()
    non_standardizable = (df["match_method"] == "non_standardizable_entity").sum()
    matched = total - unmatched - non_standardizable

    print(f"Total records:            {total}")
    print(f"Matched (standardized):   {matched}")
    print(f"Non-standardizable:       {non_standardizable}")
    print(f"Unmatched (needs review): {unmatched}")
    print(f"Match rate:               {matched / total * 100:.1f}%")
    print()
    print("Match method breakdown:")
    print(df["match_method"].value_counts().to_string())


if __name__ == "__main__":
    raw_df = pd.read_csv("../data/raw/sample_country_records.csv")
    result_df = standardize_dataframe(raw_df)
    result_df.to_csv("../data/processed/standardized_countries.csv", index=False)
    run_report(result_df)