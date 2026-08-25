from pathlib import Path

from sheetsweep.clean import build_cleanup_plan
from sheetsweep.duplicates import duplicate_count, unique_rows
from sheetsweep.models import CleanupOptions, Dataset


def dataset(rows):
    return Dataset(
        source=Path("source.csv"),
        headers=("name", "email"),
        rows=tuple(rows),
    )


def test_counts_and_removes_only_exact_duplicate_rows():
    data = dataset(
        [
            {"name": "Ada", "email": "ada@example.com"},
            {"name": "Ada", "email": "ada@example.com"},
            {"name": "Ada", "email": "other@example.com"},
        ]
    )
    assert duplicate_count(data) == 1
    assert len(unique_rows(data)) == 2


def test_cleanup_trims_normalizes_and_deduplicates_after_cleaning():
    data = dataset(
        [
            {"name": " Ada ", "email": "  "},
            {"name": "Ada", "email": ""},
        ]
    )
    plan = build_cleanup_plan(
        data,
        CleanupOptions(blank_value="N/A", remove_duplicates=True),
    )
    assert plan.rows == ({"name": "Ada", "email": "N/A"},)
    # The trimmed name and both normalized blank emails are changed cells.
    assert plan.changed_cells == 3
    assert plan.duplicate_rows_removed == 1
    assert plan.operations == (
        "trim_whitespace",
        "normalize_blanks",
        "remove_exact_duplicates",
    )


def test_cleanup_is_non_mutating_and_options_are_explicit():
    original = {"name": " Ada ", "email": ""}
    data = dataset([original])
    plan = build_cleanup_plan(
        data,
        CleanupOptions(trim_whitespace=False, normalize_blanks=False),
    )
    assert plan.rows[0]["name"] == " Ada "
    assert original == {"name": " Ada ", "email": ""}
    assert plan.operations == ()
