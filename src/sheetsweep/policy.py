"""Reusable JSON policies for data-quality validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class PolicyError(ValueError):
    """Raised when a validation policy is missing or unsafe to interpret."""


@dataclass(frozen=True)
class ValidationPolicy:
    """Validated rules loaded from a reusable policy file."""

    required_columns: tuple[str, ...] = ()
    unique_columns: tuple[str, ...] = ()
    max_blank_percent: float | None = None


def _column_names(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise PolicyError(f"{field} must be a list of column-name strings")
    names = tuple(dict.fromkeys(item.strip() for item in value))
    if any(not name for name in names):
        raise PolicyError(f"{field} cannot contain blank column names")
    return names


def load_policy(path: str | Path) -> ValidationPolicy:
    """Load and validate a local JSON policy without reading any dataset."""

    source = Path(path)
    if not source.exists():
        raise PolicyError(f"Policy file does not exist: {source}")
    if not source.is_file():
        raise PolicyError(f"Policy path is not a file: {source}")
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise PolicyError(f"Policy is not valid UTF-8: {source}") from exc
    except json.JSONDecodeError as exc:
        raise PolicyError(f"Policy is not valid JSON at line {exc.lineno}") from exc
    except OSError as exc:
        raise PolicyError(f"Could not read policy: {source}") from exc

    if not isinstance(payload, dict):
        raise PolicyError("Policy root must be a JSON object")
    allowed = {"required_columns", "unique_columns", "max_blank_percent"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise PolicyError(f"Unknown policy field(s): {', '.join(unknown)}")

    required = _column_names(payload.get("required_columns", []), "required_columns")
    unique = _column_names(payload.get("unique_columns", []), "unique_columns")
    threshold = payload.get("max_blank_percent")
    if threshold is not None:
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
            raise PolicyError("max_blank_percent must be a number or null")
        threshold = float(threshold)
        if not 0 <= threshold <= 100:
            raise PolicyError("max_blank_percent must be between 0 and 100")

    return ValidationPolicy(
        required_columns=required,
        unique_columns=unique,
        max_blank_percent=threshold,
    )
