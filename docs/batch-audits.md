# Batch CSV audits

Sheetsweep can audit a folder of CSV files without modifying any of them.

```bash
sheetsweep batch-audit imports/
```

Each result contains the relative file path, row count, column count, and exact-duplicate count. Invalid CSVs are reported separately so one bad file does not hide results for the rest of the folder. Cell values are never included.

Use recursive discovery only when needed:

```bash
sheetsweep batch-audit imports/ --recursive
```

Narrow discovery with a file-name pattern:

```bash
sheetsweep batch-audit imports/ --pattern "daily-*.csv"
```

Patterns cannot be absolute or escape the selected directory. Discovery is deterministic and defaults to at most 100 files. Set a smaller or larger reviewed limit explicitly:

```bash
sheetsweep batch-audit imports/ --max-files 25 --json
```

The command stops before opening files if discovery exceeds the limit. It returns `0` when every matching file is valid, `1` when one or more CSVs cannot be audited, and `2` for an invalid directory, pattern, or limit.

Reports reveal file paths and structural counts. Review them before sharing even though spreadsheet contents are excluded.
