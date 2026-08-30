"""Preview-first CSV auditing, validation, and cleanup automation."""

from .batch import (
    BatchError,
    BatchReport,
    BatchSchemaChange,
    BatchSchemaFileResult,
    BatchSchemaReport,
    BatchValidationFileResult,
    BatchValidationIssue,
    BatchValidationReport,
    audit_directory,
    check_schema_directory,
    validate_directory,
)
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
    "BatchError",
    "BatchReport",
    "BatchSchemaChange",
    "BatchSchemaFileResult",
    "BatchSchemaReport",
    "BatchValidationFileResult",
    "BatchValidationIssue",
    "BatchValidationReport",
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
    "audit_directory",
    "build_schema_snapshot",
    "check_schema_directory",
    "compare_schema",
    "load_policy",
    "load_schema",
    "validate_dataset",
    "validate_directory",
]
__version__ = "0.7.0"
