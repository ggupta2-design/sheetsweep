"""Privacy-aware CSV schema snapshots and drift detection."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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


def schema_payload(snapshot: SchemaSnapshot) -> dict[str, Any]:
    """Return the stable JSON representation of a snapshot."""

    return {
        "schema_version": snapshot.schema_version,
        "columns": [
            {"name": column.name, "inferred_type": column.inferred_type}
            for column in snapshot.columns
        ],
    }


def serialize_schema(snapshot: SchemaSnapshot) -> str:
    """Serialize a snapshot deterministically."""

    return json.dumps(schema_payload(snapshot), indent=2, sort_keys=True) + "\n"


def load_schema(path: str | Path) -> SchemaSnapshot:
    """Load a strict schema snapshot without reading any CSV."""

    source = Path(path)
    if not source.exists():
        raise SchemaError(f"Schema snapshot does not exist: {source}")
    if not source.is_file():
        raise SchemaError(f"Schema snapshot path is not a file: {source}")
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise SchemaError(f"Schema snapshot is not valid UTF-8: {source}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaError(f"Schema snapshot is not valid JSON at line {exc.lineno}") from exc
    except OSError as exc:
        raise SchemaError(f"Could not read schema snapshot: {source}") from exc

    if not isinstance(payload, dict) or set(payload) != {"schema_version", "columns"}:
        raise SchemaError("Schema snapshot must contain only schema_version and columns")
    if payload["schema_version"] != 1:
        raise SchemaError(f"Unsupported schema_version: {payload['schema_version']}")
    if not isinstance(payload["columns"], list):
        raise SchemaError("columns must be a list")

    columns: list[ColumnSchema] = []
    seen: set[str] = set()
    valid_types = {"empty", "boolean", "number", "text"}
    for index, item in enumerate(payload["columns"]):
        if not isinstance(item, dict) or set(item) != {"name", "inferred_type"}:
            raise SchemaError(f"Column {index} must contain name and inferred_type")
        name = item["name"]
        inferred_type = item["inferred_type"]
        if not isinstance(name, str) or not name.strip():
            raise SchemaError(f"Column {index} name must be a nonblank string")
        name = name.strip()
        if name in seen:
            raise SchemaError(f"Duplicate schema column: {name}")
        if inferred_type not in valid_types:
            raise SchemaError(f"Unsupported inferred type for {name}: {inferred_type}")
        seen.add(name)
        columns.append(ColumnSchema(name=name, inferred_type=inferred_type))
    return SchemaSnapshot(schema_version=1, columns=tuple(columns))


def compare_schema(snapshot: SchemaSnapshot, dataset: Dataset) -> SchemaComparison:
    """Compare current structure with a saved snapshot without exposing values."""

    current = build_schema_snapshot(dataset)
    expected_by_name = {column.name: column for column in snapshot.columns}
    actual_by_name = {column.name: column for column in current.columns}
    changes: list[SchemaChange] = []

    for column in snapshot.columns:
        if column.name not in actual_by_name:
            changes.append(
                SchemaChange(
                    kind="removed",
                    column=column.name,
                    expected=column.inferred_type,
                )
            )
    for column in current.columns:
        if column.name not in expected_by_name:
            changes.append(
                SchemaChange(
                    kind="added",
                    column=column.name,
                    actual=column.inferred_type,
                )
            )
    for column in snapshot.columns:
        actual = actual_by_name.get(column.name)
        if actual is not None and actual.inferred_type != column.inferred_type:
            changes.append(
                SchemaChange(
                    kind="type_changed",
                    column=column.name,
                    expected=column.inferred_type,
                    actual=actual.inferred_type,
                )
            )

    expected_names = tuple(column.name for column in snapshot.columns)
    actual_names = tuple(column.name for column in current.columns)
    if set(expected_names) == set(actual_names) and expected_names != actual_names:
        actual_positions = {name: index for index, name in enumerate(actual_names)}
        for index, name in enumerate(expected_names):
            actual_index = actual_positions[name]
            if actual_index != index:
                changes.append(
                    SchemaChange(
                        kind="reordered",
                        column=name,
                        expected=index,
                        actual=actual_index,
                    )
                )

    return SchemaComparison(matches=not changes, changes=tuple(changes))
