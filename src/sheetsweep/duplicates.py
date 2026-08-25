"""Exact duplicate-row detection."""

from __future__ import annotations

from .models import Dataset


def row_key(row: dict[str, str], headers: tuple[str, ...]) -> tuple[str, ...]:
    """Build a stable row identity using declared column order."""

    return tuple(row[header] for header in headers)


def duplicate_count(dataset: Dataset) -> int:
    """Count rows beyond the first exact occurrence."""

    seen: set[tuple[str, ...]] = set()
    duplicates = 0
    for row in dataset.rows:
        key = row_key(row, dataset.headers)
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    return duplicates


def unique_rows(dataset: Dataset) -> tuple[dict[str, str], ...]:
    """Keep the first occurrence of each exact row, preserving order."""

    seen: set[tuple[str, ...]] = set()
    rows: list[dict[str, str]] = []
    for row in dataset.rows:
        key = row_key(row, dataset.headers)
        if key not in seen:
            seen.add(key)
            rows.append(dict(row))
    return tuple(rows)
