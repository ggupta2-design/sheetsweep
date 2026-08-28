import json

import pytest

from sheetsweep.loader import load_csv
from sheetsweep.schema import (
    ColumnSchema,
    SchemaError,
    SchemaSnapshot,
    build_schema_snapshot,
    load_schema,
    serialize_schema,
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
