from pathlib import Path

from scripts.security_test import static_validate


def test_security_static_validate_passes() -> None:
    assert static_validate(Path(".")) == []
