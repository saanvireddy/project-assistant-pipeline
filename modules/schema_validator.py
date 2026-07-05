"""
Schema validation for pipeline dataframes.

Checks a dataframe against an expected schema: required columns present,
correct dtypes, and (optionally) allowed value sets for categorical columns.
Fails loudly with a structured SchemaValidationError rather than letting
a malformed dataframe silently propagate downstream.
"""

import pandas as pd
from exceptions import SchemaValidationError, MissingColumnError


def validate_schema(df: pd.DataFrame, schema: dict, strict_types: bool = False) -> None:
    """
    Validate a dataframe against an expected schema.

    schema format:
        {
            "column_name": {"dtype": "object", "required": True, "allowed_values": None},
            ...
        }

    Raises SchemaValidationError / MissingColumnError if validation fails.
    Returns None if the dataframe passes.
    """
    missing_columns = []
    type_mismatches = {}

    for column, rules in schema.items():
        if rules.get("required", True) and column not in df.columns:
            missing_columns.append(column)
            continue

        if column not in df.columns:
            continue  # optional column, not present, fine

        expected_dtype = rules.get("dtype")
        if expected_dtype and strict_types:
            actual_dtype = str(df[column].dtype)
            # pandas 3.x reports string columns as 'str' dtype instead of
            # 'object' (used by pandas <3.0); treat these as equivalent so
            # schema checks aren't fragile to pandas version differences.
            string_like = {"object", "str"}
            if not (actual_dtype in string_like and expected_dtype in string_like) and actual_dtype != expected_dtype:
                type_mismatches[column] = {
                    "expected": expected_dtype,
                    "actual": actual_dtype,
                }

        allowed_values = rules.get("allowed_values")
        if allowed_values is not None:
            invalid_mask = ~df[column].isin(allowed_values) & df[column].notna()
            if invalid_mask.any():
                bad_values = df.loc[invalid_mask, column].unique().tolist()
                type_mismatches[column] = {
                    "issue": "invalid_values",
                    "bad_values": bad_values[:10],
                }

    if missing_columns:
        raise MissingColumnError(
            f"Schema validation failed: missing required columns {missing_columns}",
            missing_columns=missing_columns,
        )

    if type_mismatches:
        raise SchemaValidationError(
            f"Schema validation failed: type/value mismatches {list(type_mismatches.keys())}",
            type_mismatches=type_mismatches,
        )


def build_schema_report(df: pd.DataFrame, schema: dict, strict_types: bool = False) -> dict:
    """
    Non-raising version: returns a report dict instead of throwing.
    Useful for logging/dashboards where you want to see all issues at once
    rather than stopping at the first one.
    """
    try:
        validate_schema(df, schema, strict_types=strict_types)
        return {"passed": True, "missing_columns": [], "type_mismatches": {}}
    except SchemaValidationError as e:
        return {
            "passed": False,
            "missing_columns": getattr(e, "missing_columns", []),
            "type_mismatches": getattr(e, "type_mismatches", {}),
        }
