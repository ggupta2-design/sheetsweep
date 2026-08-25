"""Core data structures shared by Sheetsweep features."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Dataset:
    """A validated CSV dataset held in memory."""

    source: Path
    headers: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    dialect: str = "excel"


@dataclass(frozen=True)
class CleanupOptions:
    """Explicit transformations allowed by a cleanup plan."""

    trim_whitespace: bool = True
    normalize_blanks: bool = True
    blank_value: str = ""
    remove_duplicates: bool = False


@dataclass(frozen=True)
class Profile:
    """A non-mutating summary of a dataset."""

    source: str
    row_count: int
    column_count: int
    columns: tuple[dict[str, Any], ...]
    duplicate_rows: int = 0


@dataclass(frozen=True)
class CleanupPlan:
    """The proposed result of applying cleanup options."""

    source: Path
    headers: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    original_rows: int
    changed_cells: int
    duplicate_rows_removed: int
    operations: tuple[str, ...] = field(default_factory=tuple)
