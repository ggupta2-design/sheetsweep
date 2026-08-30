"""Sheetsweep command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .batch import (
    audit_directory,
    check_schema_directory,
    format_batch_report,
    format_batch_schema,
    format_batch_validation,
    validate_directory,
)
from .clean import build_cleanup_plan
from .loader import DatasetError, load_csv
from .models import CleanupOptions
from .policy import ValidationPolicy, format_policy, load_policy, merge_policy
from .profile import profile_dataset
from .report import format_plan, format_profile, format_validation
from .schema import (
    SchemaError,
    build_schema_snapshot,
    compare_schema,
    format_comparison,
    format_schema,
    load_schema,
    write_schema,
)
from .validation import validate_dataset
from .writer import OutputError, write_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sheetsweep", description="Audit and clean CSV files safely")
    parser.add_argument("--version", action="version", version="sheetsweep 0.6.0")
    commands = parser.add_subparsers(dest="command", required=True)

    batch_audit = commands.add_parser(
        "batch-audit",
        help="audit a bounded folder of CSV files without changing them",
    )
    batch_audit.add_argument("root", type=Path)
    batch_audit.add_argument("--recursive", action="store_true")
    batch_audit.add_argument("--pattern", default="*.csv")
    batch_audit.add_argument("--max-files", type=int, default=100)
    batch_audit.add_argument("--json", action="store_true", dest="as_json")

    batch_validate = commands.add_parser(
        "batch-validate",
        help="apply one policy to a bounded folder of CSV files",
    )
    batch_validate.add_argument("root", type=Path)
    batch_validate.add_argument("--policy", type=Path, required=True)
    batch_validate.add_argument("--recursive", action="store_true")
    batch_validate.add_argument("--pattern", default="*.csv")
    batch_validate.add_argument("--max-files", type=int, default=100)
    batch_validate.add_argument(
        "--require-column",
        action="append",
        default=[],
        metavar="NAME",
        help="add a required column to the policy; may be repeated",
    )
    batch_validate.add_argument(
        "--unique-column",
        action="append",
        default=[],
        metavar="NAME",
        help="add a unique column to the policy; may be repeated",
    )
    batch_validate.add_argument(
        "--max-blank-percent",
        type=float,
        metavar="PERCENT",
        help="override the policy blank-rate limit",
    )
    batch_validate.add_argument("--json", action="store_true", dest="as_json")

    batch_schema = commands.add_parser(
        "batch-check-schema",
        help="compare a bounded folder with one saved schema baseline",
    )
    batch_schema.add_argument("root", type=Path)
    batch_schema.add_argument("--schema", type=Path, required=True)
    batch_schema.add_argument("--recursive", action="store_true")
    batch_schema.add_argument("--pattern", default="*.csv")
    batch_schema.add_argument("--max-files", type=int, default=100)
    batch_schema.add_argument("--json", action="store_true", dest="as_json")

    check_policy = commands.add_parser(
        "check-policy",
        help="validate a JSON policy without reading a CSV",
    )
    check_policy.add_argument("policy", type=Path)
    check_policy.add_argument("--json", action="store_true", dest="as_json")

    snapshot_schema = commands.add_parser(
        "snapshot-schema",
        help="preview or save a value-free CSV schema baseline",
    )
    snapshot_schema.add_argument("source", type=Path)
    snapshot_schema.add_argument("--output", type=Path)
    snapshot_schema.add_argument("--json", action="store_true", dest="as_json")
    snapshot_schema.add_argument("--apply", action="store_true", help="write the baseline")
    snapshot_schema.add_argument("--overwrite", action="store_true")

    check_schema = commands.add_parser(
        "check-schema",
        help="compare a CSV with a saved schema baseline",
    )
    check_schema.add_argument("source", type=Path)
    check_schema.add_argument("--schema", type=Path, required=True)
    check_schema.add_argument("--json", action="store_true", dest="as_json")

    audit = commands.add_parser("audit", help="inspect a CSV without changing it")
    audit.add_argument("source", type=Path)
    audit.add_argument("--json", action="store_true", dest="as_json")

    validate = commands.add_parser("validate", help="check explicit data-quality expectations")
    validate.add_argument("source", type=Path)
    validate.add_argument("--policy", type=Path, help="load reusable validation rules from JSON")
    validate.add_argument(
        "--require-column",
        action="append",
        default=[],
        metavar="NAME",
        help="require a named column; may be repeated",
    )
    validate.add_argument(
        "--max-blank-percent",
        type=float,
        metavar="PERCENT",
        help="fail columns whose blank rate is above this percentage",
    )
    validate.add_argument(
        "--unique-column",
        action="append",
        default=[],
        metavar="NAME",
        help="require nonblank values in a column to be unique; may be repeated",
    )
    validate.add_argument("--json", action="store_true", dest="as_json")

    clean = commands.add_parser("clean", help="preview or write a cleaned CSV")
    clean.add_argument("source", type=Path)
    clean.add_argument("--output", type=Path)
    clean.add_argument("--remove-duplicates", action="store_true")
    clean.add_argument("--keep-whitespace", action="store_true")
    clean.add_argument("--blank-value", default="")
    clean.add_argument("--json", action="store_true", dest="as_json")
    clean.add_argument("--apply", action="store_true", help="write the output after previewing")
    clean.add_argument("--overwrite", action="store_true", help="replace an existing output file")
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "batch-audit":
            report = audit_directory(
                args.root,
                recursive=args.recursive,
                pattern=args.pattern,
                max_files=args.max_files,
            )
            print(format_batch_report(report, as_json=args.as_json))
            return 0 if report.failed == 0 else 1
        if args.command == "batch-validate":
            policy = merge_policy(
                load_policy(args.policy),
                required_columns=tuple(args.require_column),
                unique_columns=tuple(args.unique_column),
                max_blank_percent=args.max_blank_percent,
            )
            report = validate_directory(
                args.root,
                policy,
                recursive=args.recursive,
                pattern=args.pattern,
                max_files=args.max_files,
            )
            print(format_batch_validation(report, as_json=args.as_json))
            return 0 if report.failed == 0 and report.errors == 0 else 1
        if args.command == "batch-check-schema":
            report = check_schema_directory(
                args.root,
                load_schema(args.schema),
                recursive=args.recursive,
                pattern=args.pattern,
                max_files=args.max_files,
            )
            print(format_batch_schema(report, as_json=args.as_json))
            return 0 if report.drifted == 0 and report.errors == 0 else 1
        if args.command == "check-policy":
            print(format_policy(load_policy(args.policy), as_json=args.as_json))
            return 0

        dataset = load_csv(args.source)
        if args.command == "audit":
            print(format_profile(profile_dataset(dataset), as_json=args.as_json))
            return 0
        if args.command == "snapshot-schema":
            snapshot = build_schema_snapshot(dataset)
            print(format_schema(snapshot, as_json=args.as_json))
            if not args.apply:
                print("Preview only; no schema snapshot was written.", file=sys.stderr)
                return 0
            if args.output is None:
                raise SchemaError("--output is required with --apply")
            written = write_schema(snapshot, args.output, overwrite=args.overwrite)
            print(f"Wrote schema snapshot: {written}", file=sys.stderr)
            return 0
        if args.command == "check-schema":
            comparison = compare_schema(load_schema(args.schema), dataset)
            print(format_comparison(comparison, as_json=args.as_json))
            return 0 if comparison.matches else 1
        if args.command == "validate":
            base_policy = load_policy(args.policy) if args.policy else ValidationPolicy()
            policy = merge_policy(
                base_policy,
                required_columns=tuple(args.require_column),
                max_blank_percent=args.max_blank_percent,
                unique_columns=tuple(args.unique_column),
            )
            report = validate_dataset(
                dataset,
                required_columns=policy.required_columns,
                max_blank_percent=policy.max_blank_percent,
                unique_columns=policy.unique_columns,
            )
            print(format_validation(report, as_json=args.as_json))
            return 0 if report.passed else 1

        options = CleanupOptions(
            trim_whitespace=not args.keep_whitespace,
            normalize_blanks=True,
            blank_value=args.blank_value,
            remove_duplicates=args.remove_duplicates,
        )
        plan = build_cleanup_plan(dataset, options)
        print(format_plan(plan, as_json=args.as_json))
        if not args.apply:
            print("Preview only; no file was written.", file=sys.stderr)
            return 0
        if args.output is None:
            raise OutputError("--output is required with --apply")
        written = write_plan(plan, args.output, overwrite=args.overwrite)
        print(f"Wrote cleaned CSV: {written}", file=sys.stderr)
        return 0
    except (DatasetError, OutputError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
