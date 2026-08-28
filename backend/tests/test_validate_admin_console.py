from pathlib import Path

from scripts.validate_admin_console import validate


def test_validate_admin_console_contract_passes() -> None:
    assert validate(Path(".")) == []
