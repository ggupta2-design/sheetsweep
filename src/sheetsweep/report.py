"""Human-readable and machine-readable reports."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from .models import CleanupPlan, Profile
from .validation import ValidationReport


def profile_payload(profile: Profile) -> dict[str, Any]:
    return asdict(profile)


def format_profile(profile: Profile, *, as_json: bool = False) -> str:
    """Format a dataset profile."""

    payload = profile_payload(profile)
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True)
    lines = [
        f"Source: {profile.source}",
        f"Rows: {profile.row_count}",
        f"Columns: {profile.column_count}",
        f"Exact duplicate rows: {profile.duplicate_rows}",
        "",
        "Column summary:",
    ]
    for column in profile.columns:
        lines.append(
            f"- {column['name']}: {column['type']}, "
            f"{column['blank_count']} blank, {column['unique_count']} unique"
        )
    return "\n".join(lines)


def plan_payload(plan: CleanupPlan) -> dict[str, Any]:
    return {
        "source": str(plan.source),
        "original_rows": plan.original_rows,
        "output_rows": len(plan.rows),
        "changed_cells": plan.changed_cells,
        "duplicate_rows_removed": plan.duplicate_rows_removed,
        "operations": list(plan.operations),
    }


def format_plan(plan: CleanupPlan, *, as_json: bool = False) -> str:
    """Format a cleanup preview without exposing row contents."""

    payload = plan_payload(plan)
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True)
    return "\n".join(
        [
            f"Source: {payload['source']}",
            f"Rows: {payload['original_rows']} -> {payload['output_rows']}",
            f"Changed cells: {payload['changed_cells']}",
            f"Exact duplicates removed: {payload['duplicate_rows_removed']}",
            f"Operations: {', '.join(payload['operations']) or 'none'}",
        ]
    )


def validation_payload(report: ValidationReport) -> dict[str, Any]:
    """Return a stable, automation-friendly validation payload."""

    return asdict(report)


def format_validation(report: ValidationReport, *, as_json: bool = False) -> str:
    """Format validation results without including spreadsheet values."""

    payload = validation_payload(report)
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True)
    lines = [
        f"Source: {report.source}",
        f"Rows checked: {report.row_count}",
        f"Result: {'PASS' if report.passed else 'FAIL'}",
    ]
    if not report.issues:
        lines.append("Issues: none")
    else:
        lines.append(f"Issues: {len(report.issues)}")
        for issue in report.issues:
            location = f" [{issue.column}]" if issue.column else ""
            lines.append(f"- {issue.severity.upper()} {issue.rule}{location}: {issue.message}")
    return "\n".join(lines)
