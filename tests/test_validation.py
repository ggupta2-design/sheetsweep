from pathlib import Path

import pytest

from sheetsweep.loader import load_csv
from sheetsweep.validation import validate_dataset


def dataset(tmp_path: Path, text: str):
    source = tmp_path / "data.csv"
    source.write_text(text, encoding="utf-8")
    return load_csv(source)


def test_passes_when_required_columns_and_blank_rates_are_valid(tmp_path):
    report = validate_dataset(
        dataset(tmp_path, "name,email\nAda,ada@example.com\nLin,\n"),
        required_columns=["name", "email"],
        max_blank_percent=50,
    )
    assert report.passed is True
    assert report.issues == ()


def test_reports_missing_columns_without_exposing_values(tmp_path):
    report = validate_dataset(
        dataset(tmp_path, "name\nAda\n"),
        required_columns=["name", "email"],
    )
    assert report.passed is False
    issue = report.issues[0]
    assert (issue.rule, issue.column, issue.count) == ("required_column", "email", 1)
    assert "Ada" not in issue.message


def test_reports_columns_over_the_blank_threshold(tmp_path):
    report = validate_dataset(
        dataset(tmp_path, "name,email\nAda,\nLin,\nSam,sam@example.com\n"),
        max_blank_percent=50,
    )
    issue = report.issues[0]
    assert (issue.column, issue.count) == ("email", 2)
    assert "66.7%" in issue.message


@pytest.mark.parametrize("threshold", [-1, 101])
def test_rejects_invalid_blank_thresholds(tmp_path, threshold):
    with pytest.raises(ValueError, match="between 0 and 100"):
        validate_dataset(
            dataset(tmp_path, "name\nAda\n"),
            max_blank_percent=threshold,
        )


def test_reports_repeated_values_in_unique_columns(tmp_path):
    report = validate_dataset(
        dataset(tmp_path, "id,name\n1,Ada\n1,Lin\n,Sam\n,Jo\n"),
        unique_columns=["id"],
    )
    issue = report.issues[0]
    assert (issue.rule, issue.column, issue.count) == ("unique_column", "id", 1)
    assert "Ada" not in issue.message
    assert "Lin" not in issue.message


def test_reports_missing_unique_columns(tmp_path):
    report = validate_dataset(
        dataset(tmp_path, "name\nAda\n"),
        unique_columns=["id"],
    )
    assert report.issues[0].message == "Unique column is missing: id"
