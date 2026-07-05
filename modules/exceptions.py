"""
Custom exception classes for the data pipeline.

Using specific exception types (instead of generic Exception/ValueError)
means calling code can catch and handle failure modes differently -
e.g. retry on a transient APIError but hard-stop on a SchemaValidationError.
"""


class PipelineError(Exception):
    """Base class for all pipeline-related errors."""
    pass


class SchemaValidationError(PipelineError):
    """Raised when a dataframe doesn't match its expected schema."""
    def __init__(self, message, missing_columns=None, type_mismatches=None):
        super().__init__(message)
        self.missing_columns = missing_columns or []
        self.type_mismatches = type_mismatches or {}


class DataQualityError(PipelineError):
    """Raised when data fails quality checks beyond an acceptable threshold."""
    def __init__(self, message, failed_checks=None):
        super().__init__(message)
        self.failed_checks = failed_checks or []


class MissingColumnError(SchemaValidationError):
    """Raised when a required column is absent from the dataframe."""
    pass