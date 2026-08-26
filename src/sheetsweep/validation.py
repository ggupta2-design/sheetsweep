"""Non-mutating data-quality validation rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Dataset


@dataclass(frozen=True)
class ValidationIssue:
    """A data-quality problem described without exposing cell contents."""

    rule: str
    column: str | None
    count: int
    message: str
    severity: str = "error"


@dataclass(frozen=True)
class ValidationReport:
    """Aggregate result for a read-only validation run."""

    source: str
    row_count: int
    passed: bool
    issues: tuple[ValidationIssue, ...]


def validate_dataset(
    dataset: Dataset,
    *,
    required_columns: Iterable[str] = (),
    max_blank_percent: float | None = None,
    unique_columns: Iterable[str] = (),
) -> ValidationReport:
    """Validate structure and blank rates without changing the dataset."""

    issues: list[ValidationIssue] = []
    required = tuple(dict.fromkeys(required_columns))
    missing = [name for name in required if name not in dataset.headers]
    for name in missing:
        issues.append(
            ValidationIssue(
                rule="required_column",
                column=name,
                count=1,
                message=f"Required column is missing: {name}",
            )
        )

    if max_blank_percent is not None:
        if not 0 <= max_blank_percent <= 100:
            raise ValueError("max_blank_percent must be between 0 and 100")
        total = len(dataset.rows)
        for header in dataset.headers:
            blank_count = sum(not row[header].strip() for row in dataset.rows)
            percent = (blank_count / total * 100) if total else 0.0
            if percent > max_blank_percent:
                issues.append(
                    ValidationIssue(
                        rule="max_blank_percent",
                        column=header,
                        count=blank_count,
                        message=(
                            f"Blank rate {percent:.1f}% exceeds "
                            f"{max_blank_percent:.1f}%"
                        ),
                    )
                )

    for header in tuple(dict.fromkeys(unique_columns)):
        if header not in dataset.headers:
            issues.append(
                ValidationIssue(
                    rule="unique_column",
                    column=header,
                    count=1,
                    message=f"Unique column is missing: {header}",
                )
            )
            continue
        seen: set[str] = set()
        duplicate_count = 0
        for row in dataset.rows:
            value = row[header].strip()
            if value and value in seen:
                duplicate_count += 1
            elif value:
                seen.add(value)
        if duplicate_count:
            issues.append(
                ValidationIssue(
                    rule="unique_column",
                    column=header,
                    count=duplicate_count,
                    message=f"Column contains {duplicate_count} repeated nonblank value(s)",
                )
            )

    return ValidationReport(
        source=str(dataset.source),
        row_count=len(dataset.rows),
        passed=not issues,
        issues=tuple(issues),
    )
