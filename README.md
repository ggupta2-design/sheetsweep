# Sheetsweep

Sheetsweep is a local-first command-line tool for auditing, validating, and cleaning CSV files.

It helps you understand a dataset before changing it, check explicit quality expectations, preview cleanup effects, remove exact duplicate rows, normalize whitespace and blank values, and write a separate cleaned file safely.

## Data-quality checks

Validate required columns, maximum blank rates, and unique identifiers without changing or exposing spreadsheet values:

```bash
sheetsweep validate contacts.csv \
  --require-column email \
  --unique-column contact_id \
  --max-blank-percent 10
```

Keep those rules reusable and reviewable with a versioned JSON policy:

```bash
sheetsweep check-policy examples/contacts-policy.json
sheetsweep validate contacts.csv --policy examples/contacts-policy.json
```

Catch structural changes with a value-free schema baseline:

```bash
sheetsweep snapshot-schema contacts.csv --output contacts.schema.json --apply
sheetsweep check-schema incoming.csv --schema contacts.schema.json
```

Audit a folder of CSV imports in one bounded, read-only run, then apply a
reviewed policy across the same folder:

```bash
sheetsweep batch-audit imports/ --recursive --max-files 50 --json
sheetsweep batch-validate imports/ \
  --policy examples/contacts-policy.json \
  --recursive \
  --max-files 50 \
  --json
```

Batch validation isolates quality failures and unreadable files so one bad CSV
does not hide the remaining results. Readable and JSON reports use automation-friendly exit statuses. See the [validation guide](docs/validation.md), [policy guide](docs/policies.md), [schema drift guide](docs/schema-drift.md), and [batch audit guide](docs/batch-audits.md), and [batch validation guide](docs/batch-validation.md) for details.

## Safety principles

- **Preview first:** audits, validations, and cleanup plans never modify the source file.
- **No silent overwrite:** cleaned output must be a new path unless replacement is explicitly allowed.
- **Local processing:** spreadsheet data stays on your machine.
- **Bounded batch work:** folder audits and validations enforce a reviewed maximum file count.
- **Privacy-aware reports:** validation and schema results never include cell contents.
- **Value-free baselines:** schema snapshots contain column names, order, and inferred types only.
- **Deterministic results:** identical inputs and options produce identical output.
- **Strict configuration:** unknown or unsupported policy fields are rejected.
- **Automation friendly:** reports and policy checks are available as readable text or JSON.

Sheetsweep is being built as part of an eight-week automation project challenge.
