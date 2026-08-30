# Folder-wide schema checks

Sheetsweep can compare every matching CSV in a bounded folder with one saved,
value-free schema baseline. The check is read-only and isolates unreadable files
so one bad import does not hide the remaining results.

## Create a baseline

Create a baseline from a reviewed representative CSV:

```bash
sheetsweep snapshot-schema sample.csv \
  --output baselines/import.schema.json \
  --apply
```

The snapshot contains only column names, order, and inferred types. It contains
no rows or cell values.

## Check a folder

```bash
sheetsweep batch-check-schema imports/ \
  --schema baselines/import.schema.json \
  --max-files 50
```

Use deterministic recursive discovery or a restricted pattern when needed:

```bash
sheetsweep batch-check-schema imports/ \
  --schema baselines/import.schema.json \
  --recursive \
  --pattern "daily-*.csv" \
  --json
```

The same safety rules as other batch commands apply: absolute and
parent-traversing patterns are rejected, and Sheetsweep stops before opening any
CSV when the match count exceeds `--max-files`.

## Allow optional added columns

Some upstream exports add optional fields without breaking existing consumers.
Use this narrow tolerance explicitly:

```bash
sheetsweep batch-check-schema imports/ \
  --schema baselines/import.schema.json \
  --allow-added-columns
```

Added columns are reported as tolerated. Removed, reordered, or type-changed
columns still fail the check. This option never hides the underlying change from
text or JSON output.

## Outcomes and exit statuses

Each file is reported as `MATCH`, `ALLOW`, `DRIFT`, or `ERROR`.
Status 0 means every file matched or had only explicitly allowed additions.
Status 1 means at least one file drifted or could not be loaded. Status 2 means
the baseline or batch request was invalid.

Reports include relative paths, structural change kinds, column names, expected
and actual types or positions, and input error descriptions. They never include
spreadsheet cell values. Paths and column names can still be sensitive metadata,
so review reports before publishing them.
