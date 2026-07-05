import sys
import os
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

from schema_validator import validate_schema, build_schema_report
from quality_checks import (
    check_missing_values,
    check_duplicates,
    check_out_of_range,
    check_anomalies_zscore,
    run_quality_report,
)
from exceptions import SchemaValidationError, MissingColumnError, DataQualityError


def test_schema_missing_required_column():
    df = pd.DataFrame({"a": [1, 2, 3]})
    schema = {"a": {"required": True}, "b": {"required": True}}
    with pytest.raises(MissingColumnError):
        validate_schema(df, schema)


def test_schema_optional_column_absent_ok():
    df = pd.DataFrame({"a": [1, 2, 3]})
    schema = {"a": {"required": True}, "b": {"required": False}}
    validate_schema(df, schema)


def test_schema_allowed_values_violation():
    df = pd.DataFrame({"status": ["ok", "ok", "weird"]})
    schema = {"status": {"required": True, "allowed_values": ["ok", "fail"]}}
    with pytest.raises(SchemaValidationError):
        validate_schema(df, schema)


def test_schema_report_does_not_raise():
    df = pd.DataFrame({"a": [1, 2, 3]})
    schema = {"a": {"required": True}, "b": {"required": True}}
    report = build_schema_report(df, schema)
    assert report["passed"] is False
    assert "b" in report["missing_columns"]


def test_check_missing_values():
    df = pd.DataFrame({"a": [1, None, 3]})
    result = check_missing_values(df, columns=["a"])
    assert result["a"]["missing_count"] == 1
    assert result["a"]["flagged"] is True


def test_check_duplicates():
    df = pd.DataFrame({"id": [1, 1, 2], "val": ["x", "x", "y"]})
    result = check_duplicates(df, subset=["id"])
    assert result["duplicate_count"] == 2
    assert result["flagged"] is True


def test_check_out_of_range():
    df = pd.DataFrame({"score": [10, 50, 999]})
    result = check_out_of_range(df, "score", min_val=0, max_val=100)
    assert result["out_of_range_count"] == 1
    assert result["flagged"] is True


def test_check_anomalies_zscore():
    df = pd.DataFrame({"value": [10, 12, 11, 13, 9, 11, 10, 12, 14, 500]})
    result = check_anomalies_zscore(df, "value", z_threshold=2.0)
    assert result["flagged"] is True
    assert result["anomaly_count"] >= 1


def test_run_quality_report_raises_when_configured():
    df = pd.DataFrame({"id": [1, 1], "value": [10, 20]})
    with pytest.raises(DataQualityError):
        run_quality_report(df, duplicate_subset=["id"], raise_on_failure=True)


def test_run_quality_report_passes_on_clean_data():
    df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
    report = run_quality_report(df, duplicate_subset=["id"])
    assert report["passed"] is True