# Reusable validation policies

A policy keeps validation expectations in a reviewable JSON file. It contains rules only; never put spreadsheet rows, credentials, tokens, or private cell values in a policy.

## Schema

```json
{
  "schema_version": 1,
  "name": "Contacts import",
  "required_columns": ["contact_id", "email"],
  "unique_columns": ["contact_id"],
  "max_blank_percent": 10
}
```

Sheetsweep rejects unknown fields, unsupported schema versions, blank column names, duplicate column rules, and invalid thresholds. This strict parsing prevents misspelled rules from being silently ignored.

Check a policy before processing data:

```bash
sheetsweep check-policy examples/contacts-policy.json
sheetsweep check-policy examples/contacts-policy.json --json
```

Apply it without modifying the source CSV:

```bash
sheetsweep validate contacts.csv --policy examples/contacts-policy.json
```

Command-line column rules are added to policy rules. An explicit `--max-blank-percent` replaces the policy threshold for that run. Validation still returns `0` for a pass, `1` for data-quality findings, and `2` for invalid input or policy configuration.

Policy files reveal expected column names and thresholds. Review them before publishing, even though Sheetsweep never stores spreadsheet cell values in them.
