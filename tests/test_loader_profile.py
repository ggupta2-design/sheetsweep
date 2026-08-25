from pathlib import Path

import pytest

from sheetsweep.loader import DatasetError, load_csv
from sheetsweep.profile import profile_dataset


def write_csv(tmp_path: Path, text: str, name: str = "data.csv") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_headers_and_rows_without_coercion(tmp_path):
    dataset = load_csv(write_csv(tmp_path, "name,score\nAda,10\nLin,20\n"))
    assert dataset.headers == ("name", "score")
    assert dataset.rows[0] == {"name": "Ada", "score": "10"}


def test_rejects_missing_and_empty_files(tmp_path):
    with pytest.raises(DatasetError, match="does not exist"):
        load_csv(tmp_path / "missing.csv")
    with pytest.raises(DatasetError, match="empty"):
        load_csv(write_csv(tmp_path, ""))


def test_rejects_blank_duplicate_and_overflow_headers(tmp_path):
    with pytest.raises(DatasetError, match="blank"):
        load_csv(write_csv(tmp_path, "name,\nAda,1\n"))
    with pytest.raises(DatasetError, match="unique"):
        load_csv(write_csv(tmp_path, "name,name\nAda,Lovelace\n"))
    with pytest.raises(DatasetError, match="more values"):
        load_csv(write_csv(tmp_path, "name\nAda,extra\n"))


def test_profiles_types_blanks_uniques_and_duplicates(tmp_path):
    dataset = load_csv(
        write_csv(tmp_path, "name,score,active\nAda,10,yes\nAda,,no\nAda,10,yes\n")
    )
    profile = profile_dataset(dataset)
    assert (profile.row_count, profile.column_count, profile.duplicate_rows) == (3, 3, 1)
    by_name = {column["name"]: column for column in profile.columns}
    assert by_name["score"]["type"] == "number"
    assert by_name["score"]["blank_count"] == 1
    assert by_name["active"]["type"] == "boolean"
