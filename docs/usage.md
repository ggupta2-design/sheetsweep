# Using Sheetsweep

Install in a virtual environment:

```bash
python -m pip install -e .
```

Audit a CSV without changing it:

```bash
sheetsweep audit contacts.csv
sheetsweep audit contacts.csv --json
```

Preview a cleanup:

```bash
sheetsweep clean contacts.csv --remove-duplicates
```

The preview reports counts and operations but does not expose cell contents. No file is written unless `--apply` is present.

Write a new cleaned file:

```bash
sheetsweep clean contacts.csv \
  --remove-duplicates \
  --output output/contacts.cleaned.csv \
  --apply
```

Existing output is protected. Use `--overwrite` only after reviewing the destination. Sheetsweep always refuses to replace the source CSV.


Validate expectations without changing the CSV:

```bash
sheetsweep validate contacts.csv \
  --require-column email \
  --unique-column contact_id \
  --max-blank-percent 10
```

Validation exits with status 1 when a rule fails, making it useful in automated imports and CI. Add `--json` for structured output. See [validation.md](validation.md) for rule behavior and privacy boundaries.


Reuse the same validation rules from a checked-in policy:

```bash
sheetsweep check-policy examples/contacts-policy.json
sheetsweep validate contacts.csv --policy examples/contacts-policy.json
```

You can add one-off `--require-column` and `--unique-column` rules alongside a policy. A command-line blank threshold overrides the policy threshold for that run. See [policies.md](policies.md) for the strict JSON schema and merge behavior.


Create and verify a value-free schema baseline:

```bash
sheetsweep snapshot-schema contacts.csv \
  --output baselines/contacts.schema.json \
  --apply

sheetsweep check-schema incoming.csv \
  --schema baselines/contacts.schema.json
```

Snapshot creation is preview-only without `--apply`. Schema checks return status 1 when columns are added, removed, reordered, or inferred types change. See [schema-drift.md](schema-drift.md) for details and privacy boundaries.


Audit a bounded folder of CSV files without changing them:

```bash
sheetsweep batch-audit imports/ --max-files 50
sheetsweep batch-audit imports/ --recursive --pattern "daily-*.csv" --json
```

Invalid files are isolated in the report, and the command returns status 1 when any matching CSV fails to load. See [batch-audits.md](batch-audits.md) for discovery and privacy safeguards.



Apply one reusable policy to a bounded folder:

```bash
sheetsweep batch-validate imports/ \
  --policy examples/contacts-policy.json \
  --max-files 50

sheetsweep batch-validate imports/ \
  --policy examples/contacts-policy.json \
  --recursive \
  --pattern "daily-*.csv" \
  --json
```

Quality failures and unreadable CSV files are isolated per file. The command
returns status 1 when any selected file fails or cannot be loaded, and status 2
for an invalid policy or unsafe batch request. One-run rule overrides use the
same `--require-column`, `--unique-column`, and `--max-blank-percent`
options as single-file validation. See
[batch-validation.md](batch-validation.md) for report and privacy details.



Compare a bounded import folder with one value-free schema baseline:

```bash
sheetsweep batch-check-schema imports/ \
  --schema baselines/contacts.schema.json \
  --max-files 50

sheetsweep batch-check-schema imports/ \
  --schema baselines/contacts.schema.json \
  --recursive \
  --pattern "daily-*.csv" \
  --json
```

The command returns status 1 for structural drift or unreadable files and status
2 for an invalid baseline or unsafe request. Use `--allow-added-columns` only
when optional new fields are compatible with downstream consumers; removals,
reordering, and type changes will still fail. See
[batch-schema.md](batch-schema.md) for tolerance and privacy details.
