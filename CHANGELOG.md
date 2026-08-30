# Changelog

## 0.7.0 — 2026-08-30

- Added one-baseline schema checks across bounded CSV folders.
- Added isolated match, drift, and input-error outcomes per file.
- Added value-free change details for added, removed, reordered, and type-changed columns.
- Added readable and JSON folder schema reports.
- Added an explicit tolerance for compatible added columns without hiding changes.
- Preserved deterministic discovery, safe patterns, and preflight file limits.
- Added automation-friendly exit statuses, multi-version tests, and safety documentation.

## 0.6.0 — 2026-08-29

- Added reusable policy validation across bounded CSV folders.
- Added distinct pass, quality-failure, and input-error outcomes per file.
- Added privacy-safe issue summaries with rules, columns, counts, and severities.
- Added readable and JSON batch validation reports.
- Added command-line policy extensions and blank-rate overrides.
- Preserved deterministic discovery, recursive patterns, and preflight file limits.
- Added automation-friendly exit statuses, tests, and safety documentation.

## 0.5.0 — 2026-08-28

- Added deterministic folder-level CSV discovery.
- Added recursive and file-pattern batch selection.
- Added per-file audit summaries with isolated input failures.
- Added readable and JSON batch reports without cell contents.
- Added explicit maximum file limits before any CSV is opened.
- Added automation-friendly batch success, partial-failure, and input-error statuses.
- Added multi-version tests and batch privacy guidance.

## 0.4.0 — 2026-08-28

- Added deterministic, value-free CSV schema snapshots.
- Added strict snapshot serialization and schema-version validation.
- Added detection for added, removed, reordered, and type-changed columns.
- Added privacy-safe readable and JSON drift reports.
- Added collision-safe atomic snapshot writes and preview-first CLI commands.
- Added automation-friendly schema match, drift, and input-error statuses.
- Added multi-version tests and schema drift safety guidance.

## 0.3.0 — 2026-08-27

- Added strict, reusable JSON validation policies.
- Added schema versions and human-readable policy names.
- Added deterministic merging of policy rules and command-line overrides.
- Added standalone readable and JSON policy checks.
- Added policy-driven CSV validation without modifying source data.
- Added a practical example, automated tests, and policy safety guidance.

## 0.2.0 — 2026-08-26

- Added read-only data-quality validation reports.
- Added required-column, maximum blank-rate, and unique-column rules.
- Added readable and JSON validation output without cell contents.
- Added automation-friendly pass, quality-failure, and input-error exit statuses.
- Added validation tests, CLI workflows, and privacy guidance.

## 0.1.0 — 2026-08-25

- Added safe CSV loading with delimiter detection and structural validation.
- Added read-only profiles with type hints, blank counts, unique counts, and duplicate counts.
- Added previewable whitespace, blank-value, and exact-duplicate cleanup.
- Added atomic output with source and collision protection.
- Added readable and JSON audit and cleanup reports.
- Added a preview-first CLI and explicit apply workflow.
- Added a multi-version automated test suite and safety documentation.
