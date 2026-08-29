import json

import pytest

from sheetsweep.policy import ValidationPolicy

from sheetsweep.batch import (
    BatchError,
    audit_directory,
    discover_csv_files,
    format_batch_report,
    format_batch_validation,
    validate_directory,
)


def test_discovers_csv_files_deterministically(tmp_path):
    (tmp_path / "b.csv").write_text("id\n2\n", encoding="utf-8")
    (tmp_path / "A.csv").write_text("id\n1\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "c.csv").write_text("id\n3\n", encoding="utf-8")

    assert [path.name for path in discover_csv_files(tmp_path)] == ["A.csv", "b.csv"]
    assert [
        path.relative_to(tmp_path).as_posix()
        for path in discover_csv_files(tmp_path, recursive=True)
    ] == ["A.csv", "b.csv", "nested/c.csv"]


def test_supports_explicit_file_patterns(tmp_path):
    (tmp_path / "daily-1.csv").write_text("id\n1\n", encoding="utf-8")
    (tmp_path / "archive.csv").write_text("id\n2\n", encoding="utf-8")
    assert [path.name for path in discover_csv_files(tmp_path, pattern="daily-*.csv")] == [
        "daily-1.csv"
    ]


@pytest.mark.parametrize("pattern", ["", "../*.csv", "/tmp/*.csv"])
def test_rejects_unsafe_batch_patterns(tmp_path, pattern):
    with pytest.raises(BatchError):
        discover_csv_files(tmp_path, pattern=pattern)


def test_rejects_missing_or_non_directory_roots(tmp_path):
    with pytest.raises(BatchError, match="does not exist"):
        discover_csv_files(tmp_path / "missing")
    file_path = tmp_path / "data.csv"
    file_path.write_text("id\n1\n", encoding="utf-8")
    with pytest.raises(BatchError, match="not a directory"):
        discover_csv_files(file_path)


def test_audits_files_and_isolates_invalid_csvs(tmp_path):
    (tmp_path / "good.csv").write_text("id,name\n1,Ada\n1,Ada\n", encoding="utf-8")
    (tmp_path / "bad.csv").write_text("", encoding="utf-8")

    report = audit_directory(tmp_path)
    assert (report.succeeded, report.failed) == (1, 1)
    by_path = {item.path: item for item in report.files}
    assert by_path["good.csv"].status == "ok"
    assert by_path["good.csv"].row_count == 2
    assert by_path["good.csv"].column_count == 2
    assert by_path["good.csv"].duplicate_rows == 1
    assert by_path["bad.csv"].status == "error"
    assert "empty" in by_path["bad.csv"].error


def test_batch_audit_never_exposes_cell_values(tmp_path):
    secret = "private@example.com"
    (tmp_path / "contacts.csv").write_text(
        f"email\n{secret}\n",
        encoding="utf-8",
    )
    report = audit_directory(tmp_path)
    assert secret not in repr(report)


def test_formats_batch_reports_for_people_and_automation(tmp_path):
    (tmp_path / "good.csv").write_text("id\n1\n", encoding="utf-8")
    (tmp_path / "bad.csv").write_text("", encoding="utf-8")
    report = audit_directory(tmp_path)

    text = format_batch_report(report)
    assert "Succeeded: 1" in text
    assert "Failed: 1" in text
    assert "- OK good.csv" in text
    assert "- ERROR bad.csv" in text

    payload = json.loads(format_batch_report(report, as_json=True))
    assert payload["file_count"] == 2
    assert payload["succeeded"] == 1
    assert payload["failed"] == 1
    assert {item["status"] for item in payload["files"]} == {"ok", "error"}


def test_formats_empty_batch_results(tmp_path):
    report = audit_directory(tmp_path)
    assert "no matching files" in format_batch_report(report)


def test_enforces_batch_file_limits_before_loading(tmp_path):
    for index in range(3):
        (tmp_path / f"{index}.csv").write_text("id\n1\n", encoding="utf-8")
    with pytest.raises(BatchError, match="exceeding max_files=2"):
        audit_directory(tmp_path, max_files=2)


@pytest.mark.parametrize("limit", [0, -1, True])
def test_rejects_invalid_batch_file_limits(tmp_path, limit):
    with pytest.raises(BatchError, match="positive integer"):
        discover_csv_files(tmp_path, max_files=limit)


def test_validates_folder_with_one_reusable_policy(tmp_path):
    (tmp_path / "passing.csv").write_text(
        "id,email\n1,ada@example.com\n2,lin@example.com\n",
        encoding="utf-8",
    )
    (tmp_path / "failing.csv").write_text(
        "id,email\n1,ada@example.com\n1,\n",
        encoding="utf-8",
    )
    policy = ValidationPolicy(
        name="contacts",
        required_columns=("id", "email"),
        unique_columns=("id",),
        max_blank_percent=0,
    )

    report = validate_directory(tmp_path, policy)
    assert report.policy_name == "contacts"
    assert (report.passed, report.failed, report.errors) == (1, 1, 0)
    by_path = {item.path: item for item in report.files}
    assert by_path["passing.csv"].status == "passed"
    assert by_path["passing.csv"].row_count == 2
    assert by_path["failing.csv"].status == "failed"
    assert by_path["failing.csv"].issue_count == 2
    assert set(by_path["failing.csv"].rules) == {
        "max_blank_percent",
        "unique_column",
    }


def test_batch_validation_isolates_invalid_csv_files(tmp_path):
    (tmp_path / "good.csv").write_text("id\n1\n", encoding="utf-8")
    (tmp_path / "invalid.csv").write_text("", encoding="utf-8")

    report = validate_directory(
        tmp_path,
        ValidationPolicy(required_columns=("id",)),
    )
    assert (report.passed, report.failed, report.errors) == (1, 0, 1)
    invalid = next(item for item in report.files if item.path == "invalid.csv")
    assert invalid.status == "error"
    assert "empty" in invalid.error


def test_batch_validation_issue_summaries_never_expose_cell_values(tmp_path):
    secret = "private-contact@example.com"
    (tmp_path / "contacts.csv").write_text(
        f"id,email\n1,{secret}\n1,{secret}\n",
        encoding="utf-8",
    )
    report = validate_directory(
        tmp_path,
        ValidationPolicy(unique_columns=("id", "email")),
    )

    result = report.files[0]
    assert result.status == "failed"
    assert {(issue.rule, issue.column, issue.count) for issue in result.issues} == {
        ("unique_column", "id", 1),
        ("unique_column", "email", 1),
    }
    assert secret not in repr(report)


def test_formats_batch_validation_for_people_and_automation(tmp_path):
    (tmp_path / "passing.csv").write_text("id\n1\n", encoding="utf-8")
    (tmp_path / "failing.csv").write_text("name\nAda\n", encoding="utf-8")
    report = validate_directory(
        tmp_path,
        ValidationPolicy(name="imports", required_columns=("id",)),
    )

    text = format_batch_validation(report)
    assert "Policy: imports" in text
    assert "Passed: 1" in text
    assert "Failed: 1" in text
    assert "- PASS passing.csv" in text
    assert "- FAIL failing.csv: 1 issue(s)" in text
    assert "required_column [id]: count=1" in text

    payload = json.loads(format_batch_validation(report, as_json=True))
    assert payload["policy_name"] == "imports"
    assert payload["file_count"] == 2
    assert (payload["passed"], payload["failed"], payload["errors"]) == (1, 1, 0)
    failed = next(item for item in payload["files"] if item["status"] == "failed")
    assert failed["issues"][0] == {
        "column": "id",
        "count": 1,
        "rule": "required_column",
        "severity": "error",
    }


def test_formats_empty_batch_validation_results(tmp_path):
    report = validate_directory(tmp_path, ValidationPolicy())
    assert "no matching files" in format_batch_validation(report)
