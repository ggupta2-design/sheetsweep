"""Collision-safe, atomic CSV output."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

from .models import CleanupPlan


class OutputError(ValueError):
    """Raised when a cleanup result cannot be written safely."""


def write_plan(plan: CleanupPlan, output: str | Path, *, overwrite: bool = False) -> Path:
    """Write a plan to a separate file via an atomic replace."""

    destination = Path(output)
    if destination.resolve() == plan.source.resolve():
        raise OutputError("Refusing to overwrite the source CSV")
    if destination.exists() and not overwrite:
        raise OutputError(f"Output already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=plan.headers, extrasaction="raise")
            writer.writeheader()
            writer.writerows(plan.rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except OSError as exc:
        if temporary and temporary.exists():
            temporary.unlink()
        raise OutputError(f"Could not write output: {destination}") from exc
    return destination
