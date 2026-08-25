import csv
import json
from pathlib import Path

import pytest

from sheetsweep.models import CleanupPlan, Profile
from sheetsweep.report import format_plan, format_profile
from sheetsweep.writer import OutputError, write_plan


def plan(source: Path) -> CleanupPlan:
    return CleanupPlan(
        source=source,
        headers=("name",),
        rows=({"name": "Ada"},),
        original_rows=2,
        changed_cells=1,
        duplicate_rows_removed=1,
        operations=("trim_whitespace", "remove_exact_duplicates"),
    )


def test_writer_refuses_source_and_existing_output(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("name\nAda\n", encoding="utf-8")
    with pytest.raises(OutputError, match="source"):
        write_plan(plan(source), source)

    output = tmp_path / "output.csv"
    output.write_text("keep me", encoding="utf-8")
    with pytest.raises(OutputError, match="already exists"):
        write_plan(plan(source), output)
    assert output.read_text(encoding="utf-8") == "keep me"


def test_writer_creates_parseable_output_and_allows_explicit_overwrite(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("name\nAda\n", encoding="utf-8")
    output = tmp_path / "nested" / "output.csv"
    write_plan(plan(source), output)
    with output.open(newline="", encoding="utf-8") as handle:
        assert list(csv.DictReader(handle)) == [{"name": "Ada"}]
    write_plan(plan(source), output, overwrite=True)


def test_reports_are_readable_and_machine_parseable(tmp_path):
    cleanup = plan(tmp_path / "source.csv")
    assert "Rows: 2 -> 1" in format_plan(cleanup)
    payload = json.loads(format_plan(cleanup, as_json=True))
    assert payload["duplicate_rows_removed"] == 1

    profile = Profile("source.csv", 2, 1, ({"name": "name", "type": "text", "blank_count": 0, "unique_count": 1, "most_common": "Ada"},), 1)
    assert "Exact duplicate rows: 1" in format_profile(profile)
    assert json.loads(format_profile(profile, as_json=True))["row_count"] == 2
