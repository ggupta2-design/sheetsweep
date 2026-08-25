"""Read-only dataset profiling."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation

from .duplicates import duplicate_count
from .models import Dataset, Profile


def _infer_type(values: list[str]) -> str:
    present = [value.strip() for value in values if value.strip()]
    if not present:
        return "empty"
    lowered = {value.casefold() for value in present}
    if lowered <= {"true", "false", "yes", "no"}:
        return "boolean"
    try:
        for value in present:
            Decimal(value.replace(",", ""))
        return "number"
    except InvalidOperation:
        return "text"


def profile_dataset(dataset: Dataset) -> Profile:
    """Return counts and lightweight type hints for each column."""

    columns = []
    for header in dataset.headers:
        values = [row[header] for row in dataset.rows]
        nonblank = [value for value in values if value.strip()]
        counts = Counter(nonblank)
        most_common = counts.most_common(1)
        columns.append(
            {
                "name": header,
                "type": _infer_type(values),
                "blank_count": len(values) - len(nonblank),
                "unique_count": len(set(nonblank)),
                "most_common": most_common[0][0] if most_common else None,
            }
        )
    return Profile(
        source=str(dataset.source),
        row_count=len(dataset.rows),
        column_count=len(dataset.headers),
        columns=tuple(columns),
        duplicate_rows=duplicate_count(dataset),
    )
