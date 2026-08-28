"""Preview-first CSV auditing, validation, and cleanup automation."""

from .models import CleanupOptions, Dataset, Profile
from .policy import PolicyError, ValidationPolicy, load_policy
from .schema import (
    ColumnSchema,
    SchemaComparison,
    SchemaError,
    SchemaSnapshot,
    build_schema_snapshot,
    compare_schema,
    load_schema,
)
from .validation import ValidationIssue, ValidationReport, validate_dataset

__all__ = [
    "CleanupOptions",
    "ColumnSchema",
    "Dataset",
    "Profile",
    "PolicyError",
    "SchemaComparison",
    "SchemaError",
    "SchemaSnapshot",
    "ValidationIssue",
    "ValidationPolicy",
    "ValidationReport",
    "build_schema_snapshot",
    "compare_schema",
    "load_policy",
    "load_schema",
    "validate_dataset",
]
__version__ = "0.4.0"
