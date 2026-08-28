# Schema snapshots and drift detection

Sheetsweep can save a deterministic baseline containing only column names, column order, and inferred types. It does not store row values, source paths, counts, or timestamps.

Preview a baseline:

```bash
sheetsweep snapshot-schema contacts.csv
```

Save it only after review:

```bash
sheetsweep snapshot-schema contacts.csv \
  --output baselines/contacts.schema.json \
  --apply
```

Existing snapshots are protected unless `--overwrite` is explicitly provided.

Compare a later CSV with the saved baseline:

```bash
sheetsweep check-schema new-contacts.csv \
  --schema baselines/contacts.schema.json
```

Drift reports identify:

- added columns;
- removed columns;
- changed inferred types; and
- reordered columns when the column set is unchanged.

The check returns `0` for a match, `1` for drift, and `2` for invalid CSVs, snapshots, or command options. Add `--json` for CI and import pipelines.

Type inference is deliberately lightweight. Empty columns are classified as `empty`; values are otherwise classified as `boolean`, `number`, or `text`. A changed type is a review signal, not proof that the new data is invalid.

Snapshots reveal schema names and expected types. Review them before publishing even though no cell contents are included.
