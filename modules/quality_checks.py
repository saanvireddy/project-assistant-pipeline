"""
Configurable data quality checks: missing values, duplicates,
out-of-range numeric values, and simple anomaly detection.

Design: each check returns a structured result (not just True/False) so
callers can see *what* failed and *how much*, and decide whether to raise,
log, or just flag rows for manual review.
"""

import pandas as pd
import numpy as np
from exceptions import DataQualityError


def check_missing_values(df: pd.DataFrame, columns: list = None, threshold: float = 0.0) -> dict:
    """
    Check for missing values. threshold = max acceptable fraction missing
    per column before it's flagged (0.0 = any missing value flags it).
    """
    cols = columns or df.columns.tolist()
    results = {}
    for col in cols:
        if col not in df.columns:
            continue
        missing_frac = df[col].isna().mean()
        results[col] = {
            "missing_count": int(df[col].isna().sum()),
            "missing_fraction": round(missing_frac, 4),
            "flagged": bool(missing_frac > threshold),
        }
    return results


def check_duplicates(df: pd.DataFrame, subset: list = None) -> dict:
    """Check for duplicate rows, optionally on a subset of columns (e.g. a key)."""
    dup_mask = df.duplicated(subset=subset, keep=False)
    dup_count = int(dup_mask.sum())
    return {
        "duplicate_count": dup_count,
        "duplicate_fraction": round(dup_count / len(df), 4) if len(df) else 0,
        "flagged": dup_count > 0,
        "duplicate_row_indices": df[dup_mask].index.tolist()[:20],
    }


def check_out_of_range(df: pd.DataFrame, column: str, min_val=None, max_val=None) -> dict:
    """Flag numeric values outside an expected [min_val, max_val] range."""
    if column not in df.columns:
        return {"flagged": False, "reason": "column_not_found"}

    series = df[column]
    out_of_range_mask = pd.Series(False, index=df.index)
    if min_val is not None:
        out_of_range_mask |= series < min_val
    if max_val is not None:
        out_of_range_mask |= series > max_val

    count = int(out_of_range_mask.sum())
    return {
        "out_of_range_count": count,
        "flagged": count > 0,
        "row_indices": df[out_of_range_mask].index.tolist()[:20],
    }


def check_anomalies_zscore(df: pd.DataFrame, column: str, z_threshold: float = 3.0) -> dict:
    """
    Simple anomaly detection: flag values more than z_threshold standard
    deviations from the column mean. Not a substitute for domain-specific
    anomaly detection, but catches obvious data entry errors (e.g. a stray
    extra zero).
    """
    if column not in df.columns or df[column].dropna().empty:
        return {"flagged": False, "reason": "column_not_found_or_empty"}

    series = df[column].dropna()
    mean, std = series.mean(), series.std()
    if std == 0 or np.isnan(std):
        return {"flagged": False, "anomaly_count": 0}

    z_scores = (series - mean) / std
    anomaly_mask = z_scores.abs() > z_threshold
    count = int(anomaly_mask.sum())

    return {
        "anomaly_count": count,
        "flagged": count > 0,
        "row_indices": series[anomaly_mask].index.tolist()[:20],
        "mean": round(mean, 2),
        "std": round(std, 2),
    }


def run_quality_report(
    df: pd.DataFrame,
    missing_check_columns: list = None,
    duplicate_subset: list = None,
    range_checks: dict = None,
    anomaly_columns: list = None,
    raise_on_failure: bool = False,
) -> dict:
    """
    Run the full quality check suite and return a combined report.

    range_checks format: {"column_name": {"min_val": 0, "max_val": 100}}
    """
    report = {
        "missing_values": check_missing_values(df, columns=missing_check_columns),
        "duplicates": check_duplicates(df, subset=duplicate_subset),
        "range_checks": {},
        "anomalies": {},
    }

    for col, bounds in (range_checks or {}).items():
        report["range_checks"][col] = check_out_of_range(df, col, **bounds)

    for col in (anomaly_columns or []):
        report["anomalies"][col] = check_anomalies_zscore(df, col)

    failed_checks = []
    if report["duplicates"]["flagged"]:
        failed_checks.append("duplicates")
    for col, result in report["missing_values"].items():
        if result["flagged"]:
            failed_checks.append(f"missing_values:{col}")
    for col, result in report["range_checks"].items():
        if result["flagged"]:
            failed_checks.append(f"range_check:{col}")
    for col, result in report["anomalies"].items():
        if result["flagged"]:
            failed_checks.append(f"anomaly:{col}")

    report["failed_checks"] = failed_checks
    report["passed"] = len(failed_checks) == 0

    if raise_on_failure and failed_checks:
        raise DataQualityError(
            f"Data quality checks failed: {failed_checks}", failed_checks=failed_checks
        )

    return report