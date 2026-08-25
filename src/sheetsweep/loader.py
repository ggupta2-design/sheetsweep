"""Safe CSV loading with basic structural validation."""

from __future__ import annotations

import csv
from pathlib import Path

from .models import Dataset


class DatasetError(ValueError):
    """Raised when a CSV cannot be interpreted safely."""


def load_csv(path: str | Path, *, encoding: str = "utf-8-sig") -> Dataset:
    """Load a CSV without modifying it or coercing cell values."""

    source = Path(path)
    if not source.exists():
        raise DatasetError(f"CSV file does not exist: {source}")
    if not source.is_file():
        raise DatasetError(f"CSV path is not a file: {source}")

    try:
        with source.open("r", encoding=encoding, newline="") as handle:
            sample = handle.read(8192)
            handle.seek(0)
            if not sample.strip():
                raise DatasetError("CSV file is empty")
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel
            reader = csv.DictReader(handle, dialect=dialect)
            if not reader.fieldnames:
                raise DatasetError("CSV file has no header row")
            headers = tuple(name.strip() for name in reader.fieldnames)
            if any(not name for name in headers):
                raise DatasetError("CSV headers cannot be blank")
            if len(set(headers)) != len(headers):
                raise DatasetError("CSV headers must be unique")

            rows: list[dict[str, str]] = []
            for number, row in enumerate(reader, start=2):
                if None in row:
                    raise DatasetError(f"Row {number} has more values than headers")
                normalized = {header: row.get(original, "") or "" for header, original in zip(headers, reader.fieldnames)}
                rows.append(normalized)
    except UnicodeDecodeError as exc:
        raise DatasetError(f"CSV is not valid {encoding}: {source}") from exc
    except OSError as exc:
        raise DatasetError(f"Could not read CSV: {source}") from exc

    return Dataset(source=source, headers=headers, rows=tuple(rows), dialect=getattr(dialect, "_name", "custom"))
