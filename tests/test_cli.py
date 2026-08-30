import csv
import json

from sheetsweep.cli import run


def test_audit_outputs_json(tmp_path, capsys):
    source = tmp_path / "input.csv"
    source.write_text("name,score\nAda,10\n", encoding="utf-8")
    assert run(["audit", str(source), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["row_count"] == 1
    assert payload["columns"][1]["type"] == "number"


def test_clean_defaults_to_preview_only(tmp_path, capsys):
    source = tmp_path / "input.csv"
    output = tmp_path / "clean.csv"
    source.write_text("name\n Ada \n", encoding="utf-8")
    assert run(["clean", str(source), "--output", str(output)]) == 0
    captured = capsys.readouterr()
    assert "Changed cells: 1" in captured.out
    assert "Preview only" in captured.err
    assert not output.exists()


def test_apply_requires_output_and_writes_when_explicit(tmp_path, capsys):
    source = tmp_path / "input.csv"
    source.write_text("name\n Ada \nAda\n", encoding="utf-8")
    assert run(["clean", str(source), "--apply"]) == 2
    assert "--output is required" in capsys.readouterr().err

    output = tmp_path / "clean.csv"
    result = run(
        [
            "clean",
            str(source),
            "--remove-duplicates",
            "--output",
            str(output),
            "--apply",
        ]
    )
    assert result == 0
    with output.open(newline="", encoding="utf-8") as handle:
        assert list(csv.DictReader(handle)) == [{"name": "Ada"}]


def test_cli_returns_error_for_invalid_input(tmp_path, capsys):
    assert run(["audit", str(tmp_path / "missing.csv")]) == 2
    assert "does not exist" in capsys.readouterr().err


def test_validate_returns_automation_friendly_status(tmp_path, capsys):
    source = tmp_path / "input.csv"
    source.write_text("name,email\nAda,\n", encoding="utf-8")

    result = run(
        [
            "validate",
            str(source),
            "--require-column",
            "name",
            "--require-column",
            "email",
            "--max-blank-percent",
            "0",
            "--json",
        ]
    )
    assert result == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is False
    assert payload["issues"][0]["rule"] == "max_blank_percent"

    assert run(["validate", str(source), "--require-column", "name"]) == 0
    assert "Result: PASS" in capsys.readouterr().out


def test_validate_rejects_invalid_thresholds(tmp_path, capsys):
    source = tmp_path / "input.csv"
    source.write_text("name\nAda\n", encoding="utf-8")
    assert run(["validate", str(source), "--max-blank-percent", "101"]) == 2
    assert "between 0 and 100" in capsys.readouterr().err


def test_validate_unique_columns_through_cli(tmp_path, capsys):
    source = tmp_path / "input.csv"
    source.write_text("id,name\n1,Ada\n1,Lin\n", encoding="utf-8")
    assert run(["validate", str(source), "--unique-column", "id", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["issues"][0]["rule"] == "unique_column"
    assert payload["issues"][0]["count"] == 1


def test_validate_applies_policy_and_cli_overrides(tmp_path, capsys):
    source = tmp_path / "input.csv"
    source.write_text("id,email\n1,\n1,ada@example.com\n", encoding="utf-8")
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "required_columns": ["id", "email"],
                "unique_columns": ["id"],
                "max_blank_percent": 60,
            }
        ),
        encoding="utf-8",
    )

    assert run(["validate", str(source), "--policy", str(policy), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert [issue["rule"] for issue in payload["issues"]] == ["unique_column"]

    assert run(
        [
            "validate",
            str(source),
            "--policy",
            str(policy),
            "--max-blank-percent",
            "40",
            "--json",
        ]
    ) == 1
    payload = json.loads(capsys.readouterr().out)
    assert {issue["rule"] for issue in payload["issues"]} == {
        "max_blank_percent",
        "unique_column",
    }


def test_validate_reports_invalid_policy_as_input_error(tmp_path, capsys):
    source = tmp_path / "input.csv"
    source.write_text("id\n1\n", encoding="utf-8")
    policy = tmp_path / "policy.json"
    policy.write_text('{"unknown": true}', encoding="utf-8")
    assert run(["validate", str(source), "--policy", str(policy)]) == 2
    assert "Unknown policy field" in capsys.readouterr().err


def test_check_policy_validates_without_reading_csv(tmp_path, capsys):
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "name": "imports",
                "required_columns": ["id"],
            }
        ),
        encoding="utf-8",
    )
    assert run(["check-policy", str(policy), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["name"] == "imports"

    policy.write_text('{"schema_version": 99}', encoding="utf-8")
    assert run(["check-policy", str(policy)]) == 2
    assert "Unsupported policy schema_version" in capsys.readouterr().err


def test_schema_snapshot_is_preview_first_and_writes_explicitly(tmp_path, capsys):
    source = tmp_path / "input.csv"
    source.write_text("id,name\n1,Ada\n", encoding="utf-8")
    output = tmp_path / "schema.json"

    assert run(["snapshot-schema", str(source), "--output", str(output)]) == 0
    captured = capsys.readouterr()
    assert "Schema version: 1" in captured.out
    assert "Preview only" in captured.err
    assert not output.exists()

    assert run(
        [
            "snapshot-schema",
            str(source),
            "--output",
            str(output),
            "--apply",
            "--json",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["columns"][0] == {"name": "id", "inferred_type": "number"}
    assert output.exists()


def test_check_schema_uses_drift_exit_statuses(tmp_path, capsys):
    source = tmp_path / "input.csv"
    source.write_text("id,name\n1,Ada\n", encoding="utf-8")
    schema = tmp_path / "schema.json"
    assert run(
        [
            "snapshot-schema",
            str(source),
            "--output",
            str(schema),
            "--apply",
        ]
    ) == 0
    capsys.readouterr()

    assert run(["check-schema", str(source), "--schema", str(schema), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["matches"] is True

    source.write_text("id,email\none,ada@example.com\n", encoding="utf-8")
    assert run(["check-schema", str(source), "--schema", str(schema), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["matches"] is False
    assert {change["kind"] for change in payload["changes"]} == {
        "removed",
        "added",
        "type_changed",
    }


def test_schema_commands_report_input_errors(tmp_path, capsys):
    source = tmp_path / "input.csv"
    source.write_text("id\n1\n", encoding="utf-8")
    assert run(["snapshot-schema", str(source), "--apply"]) == 2
    assert "--output is required" in capsys.readouterr().err
    assert run(
        ["check-schema", str(source), "--schema", str(tmp_path / "missing.json")]
    ) == 2
    assert "does not exist" in capsys.readouterr().err


def test_batch_audit_reports_successes_and_failures(tmp_path, capsys):
    (tmp_path / "good.csv").write_text("id\n1\n", encoding="utf-8")
    (tmp_path / "bad.csv").write_text("", encoding="utf-8")

    assert run(["batch-audit", str(tmp_path), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["file_count"] == 2
    assert (payload["succeeded"], payload["failed"]) == (1, 1)

    (tmp_path / "bad.csv").unlink()
    assert run(["batch-audit", str(tmp_path)]) == 0
    assert "Succeeded: 1" in capsys.readouterr().out


def test_batch_audit_supports_recursive_patterns_and_limits(tmp_path, capsys):
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "daily.csv").write_text("id\n1\n", encoding="utf-8")
    (nested / "archive.csv").write_text("id\n2\n", encoding="utf-8")

    assert run(
        [
            "batch-audit",
            str(tmp_path),
            "--recursive",
            "--pattern",
            "daily-*.csv",
            "--json",
        ]
    ) == 0
    assert json.loads(capsys.readouterr().out)["file_count"] == 0

    assert run(
        [
            "batch-audit",
            str(tmp_path),
            "--recursive",
            "--max-files",
            "1",
        ]
    ) == 2
    assert "exceeding max_files=1" in capsys.readouterr().err


def test_batch_validate_applies_policy_with_exit_statuses(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    (data / "passing.csv").write_text("id\n1\n2\n", encoding="utf-8")
    (data / "failing.csv").write_text("id\n1\n1\n", encoding="utf-8")
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps({"name": "daily-imports", "unique_columns": ["id"]}),
        encoding="utf-8",
    )

    assert run(
        [
            "batch-validate",
            str(data),
            "--policy",
            str(policy),
            "--json",
        ]
    ) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["policy_name"] == "daily-imports"
    assert (payload["passed"], payload["failed"], payload["errors"]) == (1, 1, 0)

    (data / "failing.csv").unlink()
    assert run(["batch-validate", str(data), "--policy", str(policy)]) == 0
    assert "Passed: 1" in capsys.readouterr().out


def test_batch_validate_isolates_invalid_files(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    (data / "invalid.csv").write_text("", encoding="utf-8")
    policy = tmp_path / "policy.json"
    policy.write_text("{}", encoding="utf-8")

    assert run(
        ["batch-validate", str(data), "--policy", str(policy), "--json"]
    ) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["errors"] == 1
    assert payload["files"][0]["status"] == "error"


def test_batch_validate_rejects_invalid_policy_and_unsafe_scope(tmp_path, capsys):
    policy = tmp_path / "policy.json"
    policy.write_text('{"unknown": true}', encoding="utf-8")
    assert run(["batch-validate", str(tmp_path), "--policy", str(policy)]) == 2
    assert "Unknown policy field" in capsys.readouterr().err

    policy.write_text("{}", encoding="utf-8")
    assert run(
        [
            "batch-validate",
            str(tmp_path),
            "--policy",
            str(policy),
            "--pattern",
            "../*.csv",
        ]
    ) == 2
    assert "stay within" in capsys.readouterr().err


def test_batch_validate_merges_explicit_policy_overrides(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    (data / "contacts.csv").write_text(
        "id,email\n1,\n1,ada@example.com\n",
        encoding="utf-8",
    )
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps({"required_columns": ["id"], "max_blank_percent": 60}),
        encoding="utf-8",
    )

    assert run(
        [
            "batch-validate",
            str(data),
            "--policy",
            str(policy),
            "--require-column",
            "email",
            "--unique-column",
            "id",
            "--max-blank-percent",
            "40",
            "--json",
        ]
    ) == 1
    payload = json.loads(capsys.readouterr().out)
    issues = payload["files"][0]["issues"]
    assert {issue["rule"] for issue in issues} == {
        "max_blank_percent",
        "unique_column",
    }


def test_batch_validate_rejects_invalid_override_threshold(tmp_path, capsys):
    policy = tmp_path / "policy.json"
    policy.write_text("{}", encoding="utf-8")
    assert run(
        [
            "batch-validate",
            str(tmp_path),
            "--policy",
            str(policy),
            "--max-blank-percent",
            "101",
        ]
    ) == 2
    assert "between 0 and 100" in capsys.readouterr().err


def test_batch_check_schema_reports_drift_with_exit_status(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    matching = data / "matching.csv"
    matching.write_text("id,name\n1,Ada\n", encoding="utf-8")
    (data / "drifted.csv").write_text("id,email\none,Ada\n", encoding="utf-8")
    schema = tmp_path / "schema.json"
    assert run(
        [
            "snapshot-schema",
            str(matching),
            "--output",
            str(schema),
            "--apply",
        ]
    ) == 0
    capsys.readouterr()

    assert run(
        [
            "batch-check-schema",
            str(data),
            "--schema",
            str(schema),
            "--json",
        ]
    ) == 1
    payload = json.loads(capsys.readouterr().out)
    assert (payload["matched"], payload["drifted"], payload["errors"]) == (1, 1, 0)

    (data / "drifted.csv").unlink()
    assert run(["batch-check-schema", str(data), "--schema", str(schema)]) == 0
    assert "Matched: 1" in capsys.readouterr().out


def test_batch_check_schema_isolates_input_errors(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    source = data / "source.csv"
    source.write_text("id\n1\n", encoding="utf-8")
    schema = tmp_path / "schema.json"
    assert run(
        ["snapshot-schema", str(source), "--output", str(schema), "--apply"]
    ) == 0
    capsys.readouterr()
    source.write_text("", encoding="utf-8")

    assert run(
        ["batch-check-schema", str(data), "--schema", str(schema), "--json"]
    ) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["errors"] == 1
    assert payload["files"][0]["status"] == "error"


def test_batch_check_schema_rejects_invalid_scope_and_baseline(tmp_path, capsys):
    missing = tmp_path / "missing.schema.json"
    assert run(
        ["batch-check-schema", str(tmp_path), "--schema", str(missing)]
    ) == 2
    assert "does not exist" in capsys.readouterr().err

    schema = tmp_path / "schema.json"
    schema.write_text('{"schema_version": 99, "columns": []}', encoding="utf-8")
    assert run(
        ["batch-check-schema", str(tmp_path), "--schema", str(schema)]
    ) == 2
    assert "Unsupported schema_version" in capsys.readouterr().err
