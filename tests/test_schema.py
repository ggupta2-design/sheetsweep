import json

import pytest

from sheetsweep.loader import load_csv
from sheetsweep.schema import (
    ColumnSchema,
    SchemaError,
    SchemaSnapshot,
    build_schema_snapshot,
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
