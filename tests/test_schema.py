import json

import pytest

from sheetsweep.loader import load_csv
from sheetsweep.schema import (
    ColumnSchema,
    SchemaError,
    SchemaSnapshot,
    build_schema_snapshot,
    compare_schema,
    format_comparison,
    format_schema,
    load_schema,
    serialize_schema,
    write_schema,
)


def csv_dataset(tmp_path, text, name="data.csv"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return load_csv(path)


def test_builds_value_free_schema_snapshot(tmp_path):
    snapshot = build_schema_snapshot(
        csv_dataset(tmp_path, "id,name,active\n1,Ada,true\n2,Lin,false\n")
    )
    assert snapshot == SchemaSnapshot(
        schema_version=1,
        columns=(
            ColumnSchema("id", "number"),
            ColumnSchema("name", "text"),
            ColumnSchema("active", "boolean"),
        ),
    )
    rendered = repr(snapshot)
    assert "Ada" not in rendered
    assert "Lin" not in rendered


def test_snapshot_is_deterministic_for_equivalent_types(tmp_path):
    first = build_schema_snapshot(csv_dataset(tmp_path, "id,name\n1,Ada\n", "one.csv"))
    second = build_schema_snapshot(csv_dataset(tmp_path, "id,name\n99,Grace\n", "two.csv"))
    assert first == second


def test_serializes_and_loads_schema_round_trip(tmp_path):
    snapshot = SchemaSnapshot(
        schema_version=1,
        columns=(ColumnSchema("id", "number"), ColumnSchema("name", "text")),
    )
    path = tmp_path / "schema.json"
    path.write_text(serialize_schema(snapshot), encoding="utf-8")
    assert load_schema(path) == snapshot
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert set(payload) == {"schema_version", "columns"}


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"schema_version": 2, "columns": []}, "Unsupported"),
        ({"schema_version": 1, "columns": "id"}, "must be a list"),
        (
            {
                "schema_version": 1,
                "columns": [
                    {"name": "id", "inferred_type": "number"},
                    {"name": "id", "inferred_type": "number"},
                ],
            },
            "Duplicate",
        ),
        (
            {
                "schema_version": 1,
                "columns": [{"name": "id", "inferred_type": "secret"}],
            },
            "Unsupported inferred type",
        ),
        ({"schema_version": 1, "columns": [], "extra": True}, "contain only"),
    ],
)
def test_rejects_ambiguous_or_unsupported_snapshots(tmp_path, payload, message):
    path = tmp_path / "schema.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SchemaError, match=message):
        load_schema(path)


def test_detects_added_removed_and_type_changed_columns(tmp_path):
    baseline = SchemaSnapshot(
        schema_version=1,
        columns=(
            ColumnSchema("id", "number"),
            ColumnSchema("name", "text"),
            ColumnSchema("active", "boolean"),
        ),
    )
    dataset = csv_dataset(tmp_path, "id,email,active\none,ada@example.com,true\n")
    comparison = compare_schema(baseline, dataset)
    assert comparison.matches is False
    assert [(change.kind, change.column) for change in comparison.changes] == [
        ("removed", "name"),
        ("added", "email"),
        ("type_changed", "id"),
    ]


def test_detects_column_reordering_only_when_sets_match(tmp_path):
    baseline = SchemaSnapshot(
        schema_version=1,
        columns=(ColumnSchema("id", "number"), ColumnSchema("name", "text")),
    )
    comparison = compare_schema(baseline, csv_dataset(tmp_path, "name,id\nAda,1\n"))
    assert [(change.kind, change.column) for change in comparison.changes] == [
        ("reordered", "id"),
        ("reordered", "name"),
    ]


def test_reports_matching_schema(tmp_path):
    baseline = SchemaSnapshot(
        schema_version=1,
        columns=(ColumnSchema("id", "number"), ColumnSchema("name", "text")),
    )
    comparison = compare_schema(baseline, csv_dataset(tmp_path, "id,name\n2,Lin\n"))
    assert comparison.matches is True
    assert comparison.changes == ()


def test_formats_schema_and_drift_without_values(tmp_path):
    baseline = SchemaSnapshot(
        schema_version=1,
        columns=(ColumnSchema("id", "number"), ColumnSchema("name", "text")),
    )
    dataset = csv_dataset(tmp_path, "id,email\none,private@example.com\n")
    comparison = compare_schema(baseline, dataset)

    schema_text = format_schema(baseline)
    assert "- id: number" in schema_text
    drift_text = format_comparison(comparison)
    assert "Result: DRIFT" in drift_text
    assert "private@example.com" not in drift_text

    payload = json.loads(format_comparison(comparison, as_json=True))
    assert payload["matches"] is False
    assert {change["kind"] for change in payload["changes"]} == {
        "removed",
        "added",
        "type_changed",
    }


def test_writes_schema_atomically_and_protects_existing_files(tmp_path):
    snapshot = SchemaSnapshot(
        schema_version=1,
        columns=(ColumnSchema("id", "number"),),
    )
    output = tmp_path / "baselines" / "schema.json"
    assert write_schema(snapshot, output) == output
    assert load_schema(output) == snapshot

    with pytest.raises(SchemaError, match="already exists"):
        write_schema(
            SchemaSnapshot(1, (ColumnSchema("email", "text"),)),
            output,
        )
    assert load_schema(output) == snapshot

    replacement = SchemaSnapshot(1, (ColumnSchema("email", "text"),))
    write_schema(replacement, output, overwrite=True)
    assert load_schema(output) == replacement
