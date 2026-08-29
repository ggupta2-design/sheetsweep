# Policy-based batch validation

Sheetsweep can apply one reviewed validation policy to every matching CSV in a
bounded folder. The operation is read-only: files are discovered
deterministically, loaded one at a time, and never changed.

## Validate a folder

```bash
sheetsweep batch-validate imports/ \
  --policy examples/contacts-policy.json \
  --max-files 50
```

Use `--recursive` to include subdirectories and `--pattern` to restrict the
selection:

```bash
sheetsweep batch-validate imports/ \
  --policy examples/contacts-policy.json \
  --recursive \
  --pattern "daily-*.csv" \
  --json
```

Discovery rejects absolute or parent-traversing patterns. The command stops
before opening any CSV when the match count exceeds `--max-files`.

## Add one-run overrides

Explicit rules extend the policy for a single run. An explicit blank threshold
replaces the policy threshold:

```bash
sheetsweep batch-validate imports/ \
  --policy examples/contacts-policy.json \
  --require-column imported_at \
  --unique-column contact_id \
  --max-blank-percent 5
```

## Results and exit statuses

Each file is reported as:

- `PASS` when all rules pass.
- `FAIL` when the CSV loads but violates one or more quality rules.
- `ERROR` when the CSV cannot be loaded safely.

One bad file does not prevent later files from being checked. Exit status 0
means every selected file passed, status 1 means at least one file failed or
could not be loaded, and status 2 means the policy or batch request itself was
invalid.

## Privacy boundaries

Reports contain relative paths, row counts, rule names, affected column names,
issue counts, severities, and input error descriptions. They do not contain
spreadsheet cell values. Paths and column names can still be sensitive metadata,
so review JSON output before publishing it.
