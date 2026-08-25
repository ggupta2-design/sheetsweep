# Sheetsweep

Sheetsweep is a local-first command-line tool for auditing and cleaning CSV files.

It helps you understand a dataset before changing it, preview cleanup effects, remove exact duplicate rows, normalize whitespace and blank values, and write a separate cleaned file safely.

## Safety principles

- **Preview first:** audits and cleanup plans never modify the source file.
- **No silent overwrite:** cleaned output must be a new path unless replacement is explicitly allowed.
- **Local processing:** spreadsheet data stays on your machine.
- **Deterministic results:** identical inputs and options produce identical output.
- **Automation friendly:** reports are available as readable text or JSON.

Sheetsweep 0.1 is being built as part of an eight-week automation project challenge.
