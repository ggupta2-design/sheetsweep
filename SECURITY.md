# Security and privacy

Sheetsweep is designed to process CSV data locally. It does not make network requests, upload files, or collect telemetry.

## Safe use

- Review the cleanup preview before using `--apply`.
- Write to a separate output path and retain the source as a backup.
- Treat CSV files as potentially sensitive; do not commit personal or confidential data.
- Spreadsheet formulas are preserved as text in CSV output. Opening untrusted output in spreadsheet software can still trigger formula-injection risks.
- Exact duplicate removal compares complete rows after enabled cleanup transformations.

## Reporting vulnerabilities

Please use GitHub's private vulnerability reporting feature when available. Do not include real sensitive spreadsheet data in a public issue.
