from pathlib import Path

from scripts.docker_integration_test import SERVICE_PORTS, static_validate


def test_docker_integration_static_validation_passes() -> None:
    assert static_validate(Path("."), "auth-service") == []


def test_docker_integration_uses_lightweight_service() -> None:
    assert SERVICE_PORTS["auth-service"] == 8002
