"""Read-only batch discovery and auditing for CSV folders."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .loader import DatasetError, load_csv
from .policy import ValidationPolicy
from .profile import profile_dataset
from .schema import SchemaSnapshot, compare_schema
from .validation import validate_dataset


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


@dataclass(frozen=True)
class BatchValidationIssue:
    """Privacy-safe issue summary without spreadsheet cell contents."""

    rule: str
    column: str | None
    count: int
    severity: str


@dataclass(frozen=True)
class BatchValidationFileResult:
    """Value-free policy validation outcome for one CSV file."""

    path: str
    status: str
    row_count: int | None = None
    issue_count: int = 0
    rules: tuple[str, ...] = ()
    issues: tuple[BatchValidationIssue, ...] = ()
    error: str | None = None


@dataclass(frozen=True)
class BatchValidationReport:
    """Aggregate policy validation result for a bounded CSV folder."""

    root: str
    recursive: bool
    pattern: str
    policy_name: str | None
    files: tuple[BatchValidationFileResult, ...]
    passed: int
    failed: int
    errors: int


@dataclass(frozen=True)
class BatchSchemaChange:
    """Value-free structural change found in one CSV."""

    kind: str
    column: str
    expected: str | int | None = None
    actual: str | int | None = None


@dataclass(frozen=True)
class BatchSchemaFileResult:
    """Schema comparison outcome for one CSV file."""

    path: str
    status: str
    change_count: int = 0
    change_kinds: tuple[str, ...] = ()
    changes: tuple[BatchSchemaChange, ...] = ()
    error: str | None = None


@dataclass(frozen=True)
class BatchSchemaReport:
    """Aggregate schema comparison for a bounded CSV folder."""

    root: str
    recursive: bool
    pattern: str
    files: tuple[BatchSchemaFileResult, ...]
    matched: int
    drifted: int
    errors: int


def discover_csv_files(
    root: str | Path,
    *,
    recursive: bool = False,
    pattern: str = "*.csv",
    max_files: int = 100,
) -> tuple[Path, ...]:
    """Find matching files deterministically without opening them."""

    directory = Path(root)
    if not directory.exists():
        raise BatchError(f"Batch directory does not exist: {directory}")
    if not directory.is_dir():
        raise BatchError(f"Batch path is not a directory: {directory}")
    if isinstance(max_files, bool) or max_files < 1:
        raise BatchError("max_files must be a positive integer")
    if not pattern.strip():
        raise BatchError("Batch pattern cannot be blank")
    candidate = Path(pattern)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise BatchError("Batch pattern must stay within the selected directory")

    matches = directory.rglob(pattern) if recursive else directory.glob(pattern)
    discovered = tuple(
        sorted(
            (path for path in matches if path.is_file()),
            key=lambda path: path.relative_to(directory).as_posix().casefold(),
        )
    )
    if len(discovered) > max_files:
        raise BatchError(
            f"Batch matched {len(discovered)} files, exceeding max_files={max_files}"
        )
    return discovered


def audit_directory(
    root: str | Path,
    *,
    recursive: bool = False,
    pattern: str = "*.csv",
    max_files: int = 100,
) -> BatchReport:
    """Audit matching CSV files while isolating per-file input errors."""

    directory = Path(root)
    paths = discover_csv_files(
        directory,
        recursive=recursive,
        pattern=pattern,
        max_files=max_files,
    )
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


def validate_directory(
    root: str | Path,
    policy: ValidationPolicy,
    *,
    recursive: bool = False,
    pattern: str = "*.csv",
    max_files: int = 100,
) -> BatchValidationReport:
    """Apply one validated policy while isolating per-file input errors."""

    directory = Path(root)
    paths = discover_csv_files(
        directory,
        recursive=recursive,
        pattern=pattern,
        max_files=max_files,
    )
    results: list[BatchValidationFileResult] = []
    for path in paths:
        relative = path.relative_to(directory).as_posix()
        try:
            dataset = load_csv(path)
            validation = validate_dataset(
                dataset,
                required_columns=policy.required_columns,
                unique_columns=policy.unique_columns,
                max_blank_percent=policy.max_blank_percent,
            )
            results.append(
                BatchValidationFileResult(
                    path=relative,
                    status="passed" if validation.passed else "failed",
                    row_count=validation.row_count,
                    issue_count=len(validation.issues),
                    rules=tuple(dict.fromkeys(issue.rule for issue in validation.issues)),
                    issues=tuple(
                        BatchValidationIssue(
                            rule=issue.rule,
                            column=issue.column,
                            count=issue.count,
                            severity=issue.severity,
                        )
                        for issue in validation.issues
                    ),
                )
            )
        except DatasetError as exc:
            results.append(
                BatchValidationFileResult(
                    path=relative,
                    status="error",
                    error=str(exc),
                )
            )

    return BatchValidationReport(
        root=str(directory),
        recursive=recursive,
        pattern=pattern,
        policy_name=policy.name,
        files=tuple(results),
        passed=sum(result.status == "passed" for result in results),
        failed=sum(result.status == "failed" for result in results),
        errors=sum(result.status == "error" for result in results),
    )


def check_schema_directory(
    root: str | Path,
    snapshot: SchemaSnapshot,
    *,
    recursive: bool = False,
    pattern: str = "*.csv",
    max_files: int = 100,
) -> BatchSchemaReport:
    """Compare matching CSV files with one value-free schema baseline."""

    directory = Path(root)
    paths = discover_csv_files(
        directory,
        recursive=recursive,
        pattern=pattern,
        max_files=max_files,
    )
    results: list[BatchSchemaFileResult] = []
    for path in paths:
        relative = path.relative_to(directory).as_posix()
        try:
            comparison = compare_schema(snapshot, load_csv(path))
            changes = tuple(
                BatchSchemaChange(
                    kind=change.kind,
                    column=change.column,
                    expected=change.expected,
                    actual=change.actual,
                )
                for change in comparison.changes
            )
            results.append(
                BatchSchemaFileResult(
                    path=relative,
                    status="matched" if comparison.matches else "drifted",
                    change_count=len(changes),
                    change_kinds=tuple(dict.fromkeys(change.kind for change in changes)),
                    changes=changes,
                )
            )
        except DatasetError as exc:
            results.append(
                BatchSchemaFileResult(
                    path=relative,
                    status="error",
                    error=str(exc),
                )
            )

    return BatchSchemaReport(
        root=str(directory),
        recursive=recursive,
        pattern=pattern,
        files=tuple(results),
        matched=sum(result.status == "matched" for result in results),
        drifted=sum(result.status == "drifted" for result in results),
        errors=sum(result.status == "error" for result in results),
    )


def batch_payload(report: BatchReport) -> dict[str, object]:
    """Return a stable value-free batch summary."""

    return {
        "root": report.root,
        "recursive": report.recursive,
        "pattern": report.pattern,
        "file_count": len(report.files),
        "succeeded": report.succeeded,
        "failed": report.failed,
        "files": [asdict(result) for result in report.files],
    }


def format_batch_report(report: BatchReport, *, as_json: bool = False) -> str:
    """Format a batch audit for people or automation."""

    payload = batch_payload(report)
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True)
    lines = [
        f"Root: {report.root}",
        f"Files: {len(report.files)}",
        f"Succeeded: {report.succeeded}",
        f"Failed: {report.failed}",
    ]
    if not report.files:
        lines.append("Results: no matching files")
    else:
        lines.append("Results:")
        for result in report.files:
            if result.status == "ok":
                lines.append(
                    f"- OK {result.path}: {result.row_count} rows, "
                    f"{result.column_count} columns, "
                    f"{result.duplicate_rows} exact duplicates"
                )
            else:
                lines.append(f"- ERROR {result.path}: {result.error}")
    return "\n".join(lines)



def batch_validation_payload(report: BatchValidationReport) -> dict[str, object]:
    """Return a stable value-free policy validation summary."""

    return {
        "root": report.root,
        "recursive": report.recursive,
        "pattern": report.pattern,
        "policy_name": report.policy_name,
        "file_count": len(report.files),
        "passed": report.passed,
        "failed": report.failed,
        "errors": report.errors,
        "files": [asdict(result) for result in report.files],
    }


def format_batch_validation(
    report: BatchValidationReport,
    *,
    as_json: bool = False,
) -> str:
    """Format folder policy results for people or automation."""

    payload = batch_validation_payload(report)
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True)

    lines = [
        f"Root: {report.root}",
        f"Policy: {report.policy_name or 'unnamed'}",
        f"Files: {len(report.files)}",
        f"Passed: {report.passed}",
        f"Failed: {report.failed}",
        f"Input errors: {report.errors}",
    ]
    if not report.files:
        lines.append("Results: no matching files")
        return "\n".join(lines)

    lines.append("Results:")
    for result in report.files:
        if result.status == "passed":
            lines.append(f"- PASS {result.path}: {result.row_count} rows")
        elif result.status == "error":
            lines.append(f"- ERROR {result.path}: {result.error}")
        else:
            lines.append(
                f"- FAIL {result.path}: {result.issue_count} issue(s) "
                f"({', '.join(result.rules)})"
            )
            for issue in result.issues:
                column = f" [{issue.column}]" if issue.column else ""
                lines.append(
                    f"  - {issue.rule}{column}: count={issue.count}, "
                    f"severity={issue.severity}"
                )
    return "\n".join(lines)
