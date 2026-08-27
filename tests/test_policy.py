import json

import pytest

from sheetsweep.policy import PolicyError, ValidationPolicy, load_policy


def write_policy(tmp_path, payload, name="policy.json"):
    path = tmp_path / name
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_loads_and_normalizes_reusable_policy(tmp_path):
    policy = load_policy(
        write_policy(
            tmp_path,
            {
                "required_columns": [" id ", "email", "id"],
                "unique_columns": ["id"],
                "max_blank_percent": 12.5,
            },
        )
    )
    assert policy == ValidationPolicy(
        required_columns=("id", "email"),
        unique_columns=("id",),
        max_blank_percent=12.5,
    )


def test_uses_safe_defaults_for_empty_policy(tmp_path):
    assert load_policy(write_policy(tmp_path, {})) == ValidationPolicy()


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("[]", "root must be"),
        ('{"required_columns": "email"}', "must be a list"),
        ('{"required_columns": [" "]}', "blank column"),
        ('{"max_blank_percent": true}', "number or null"),
        ('{"max_blank_percent": 101}', "between 0 and 100"),
        ('{"secret": "value"}', "Unknown policy field"),
        ("{bad json", "not valid JSON"),
    ],
)
def test_rejects_ambiguous_or_unknown_policy_data(tmp_path, payload, message):
    with pytest.raises(PolicyError, match=message):
        load_policy(write_policy(tmp_path, payload))


def test_reports_missing_policy_files(tmp_path):
    with pytest.raises(PolicyError, match="does not exist"):
        load_policy(tmp_path / "missing.json")


def test_loads_versioned_named_policies(tmp_path):
    policy = load_policy(
        write_policy(
            tmp_path,
            {
                "schema_version": 1,
                "name": " Customer import ",
                "required_columns": ["customer_id"],
            },
        )
    )
    assert policy.schema_version == 1
    assert policy.name == "Customer import"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"schema_version": 2}, "Unsupported"),
        ({"schema_version": True}, "must be an integer"),
        ({"name": " "}, "nonblank"),
    ],
)
def test_rejects_unsupported_policy_metadata(tmp_path, payload, message):
    with pytest.raises(PolicyError, match=message):
        load_policy(write_policy(tmp_path, payload))
