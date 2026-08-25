"""Previewable CSV cleanup transformations."""

from __future__ import annotations

from .duplicates import row_key
from .models import CleanupOptions, CleanupPlan, Dataset


def build_cleanup_plan(dataset: Dataset, options: CleanupOptions) -> CleanupPlan:
    """Build a deterministic plan without writing to disk."""

    changed_cells = 0
    cleaned: list[dict[str, str]] = []
    seen: set[tuple[str, ...]] = set()
    removed = 0

    for original in dataset.rows:
        row: dict[str, str] = {}
        for header in dataset.headers:
            before = original[header]
            after = before.strip() if options.trim_whitespace else before
            if options.normalize_blanks and not after.strip():
                after = options.blank_value
            if after != before:
                changed_cells += 1
            row[header] = after

        key = row_key(row, dataset.headers)
        if options.remove_duplicates and key in seen:
            removed += 1
            continue
        seen.add(key)
        cleaned.append(row)

    operations = []
    if options.trim_whitespace:
        operations.append("trim_whitespace")
    if options.normalize_blanks:
        operations.append("normalize_blanks")
    if options.remove_duplicates:
        operations.append("remove_exact_duplicates")

    return CleanupPlan(
        source=dataset.source,
        headers=dataset.headers,
        rows=tuple(cleaned),
        original_rows=len(dataset.rows),
        changed_cells=changed_cells,
        duplicate_rows_removed=removed,
        operations=tuple(operations),
    )
