import json

import pytest

from sheetsweep.batch import BatchError, discover_csv_files


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
