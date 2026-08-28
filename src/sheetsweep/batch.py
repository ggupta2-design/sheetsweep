"""Read-only batch discovery and auditing for CSV folders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .loader import DatasetError, load_csv
from .profile import profile_dataset


class BatchError(ValueError):
    """Raised when a batch audit request is unsafe or invalid."""


@dataclass(frozen=True)
class BatchFileResult:
    """Value-free audit outcome for one CSV file."""

    path: str
    status: str
    row_count: int | None = None
    column_count: int | None = None
    duplicate_rows: int | None = None
    error: str | None = None


@dataclass(frozen=True)
class BatchReport:
    """Aggregate result for deterministic folder auditing."""

    root: str
    recursive: bool
    pattern: str
    files: tuple[BatchFileResult, ...]
    succeeded: int
    failed: int


def discover_csv_files(
    root: str | Path,
    *,
    recursive: bool = False,
    pattern: str = "*.csv",
) -> tuple[Path, ...]:
    """Find matching files deterministically without opening them."""

    directory = Path(root)
    if not directory.exists():
        raise BatchError(f"Batch directory does not exist: {directory}")
    if not directory.is_dir():
        raise BatchError(f"Batch path is not a directory: {directory}")
    if not pattern.strip():
        raise BatchError("Batch pattern cannot be blank")
    candidate = Path(pattern)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise BatchError("Batch pattern must stay within the selected directory")

    matches = directory.rglob(pattern) if recursive else directory.glob(pattern)
    return tuple(
        sorted(
            (path for path in matches if path.is_file()),
            key=lambda path: path.relative_to(directory).as_posix().casefold(),
        )
    )


def audit_directory(
    root: str | Path,
    *,
    recursive: bool = False,
    pattern: str = "*.csv",
) -> BatchReport:
    """Audit matching CSV files while isolating per-file input errors."""

    directory = Path(root)
    paths = discover_csv_files(directory, recursive=recursive, pattern=pattern)
    results: list[BatchFileResult] = []
    for path in paths:
        relative = path.relative_to(directory).as_posix()
        try:
            profile = profile_dataset(load_csv(path))
            results.append(
                BatchFileResult(
                    path=relative,
                    status="ok",
                    row_count=profile.row_count,
                    column_count=profile.column_count,
                    duplicate_rows=profile.duplicate_rows,
                )
            )
        except DatasetError as exc:
            results.append(
                BatchFileResult(
                    path=relative,
                    status="error",
                    error=str(exc),
                )
            )
    failed = sum(result.status == "error" for result in results)
    return BatchReport(
        root=str(directory),
        recursive=recursive,
        pattern=pattern,
        files=tuple(results),
        succeeded=len(results) - failed,
        failed=failed,
    )
