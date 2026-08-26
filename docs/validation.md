# Data-quality validation

Sheetsweep validation is read-only: it loads the CSV, evaluates explicit expectations, and reports counts. It never edits the source or writes a cleaned copy.

## Available rules

- `--require-column NAME` checks that a header exists.
- `--max-blank-percent PERCENT` checks every column's blank rate.
- `--unique-column NAME` checks that nonblank values do not repeat.

Repeat column options to check more than one column.

```bash
sheetsweep validate contacts.csv \
  --require-column email \
  --require-column account_id \
  --unique-column account_id \
  --max-blank-percent 10
```

The command returns exit status `0` when every rule passes, `1` when data-quality issues are found, and `2` for invalid input or command configuration. Use `--json` for CI jobs and scripts.

## Privacy boundary

Reports include source paths, column names, counts, rule names, and thresholds. They never include cell values. A report can still reveal schema information, so review it before sharing publicly.

Uniqueness checks ignore blank values; combine them with a blank-rate rule when the field must also be populated. Rules identify review candidates and do not prove that a dataset is correct or fit for a particular decision.
