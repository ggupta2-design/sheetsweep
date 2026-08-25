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
