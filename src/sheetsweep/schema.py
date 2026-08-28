"""Privacy-aware CSV schema snapshots and drift detection."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Dataset
from .profile import profile_dataset


class SchemaError(ValueError):
    """Raised when a schema snapshot cannot be interpreted safely."""


@dataclass(frozen=True)
class ColumnSchema:
    """A column name and its inferred value type."""

    name: str
    inferred_type: str


@dataclass(frozen=True)
class SchemaSnapshot:
    """A deterministic, value-free description of CSV structure."""

    schema_version: int
    columns: tuple[ColumnSchema, ...]


@dataclass(frozen=True)
class SchemaChange:
    """One structural difference between a snapshot and a dataset."""

    kind: str
    column: str
    expected: str | int | None = None
    actual: str | int | None = None


@dataclass(frozen=True)
class SchemaComparison:
    """Aggregate result of comparing live structure with a snapshot."""

    matches: bool
    changes: tuple[SchemaChange, ...]


def build_schema_snapshot(dataset: Dataset) -> SchemaSnapshot:
    """Build a snapshot without retaining source paths or cell values."""

    profile = profile_dataset(dataset)
    return SchemaSnapshot(
        schema_version=1,
        columns=tuple(
            ColumnSchema(
                name=str(column["name"]),
                inferred_type=str(column["type"]),
            )
            for column in profile.columns
        ),
    )
