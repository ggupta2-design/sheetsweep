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
