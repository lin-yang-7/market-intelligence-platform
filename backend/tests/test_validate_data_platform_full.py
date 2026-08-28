from pathlib import Path

from scripts.validate_data_platform_full import validate


def test_validate_data_platform_full_contract_passes() -> None:
    assert validate(Path(".")) == []
