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
