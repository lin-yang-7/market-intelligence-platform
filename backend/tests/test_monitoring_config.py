from pathlib import Path

from scripts.validate_monitoring_config import (
    REQUIRED_PROMETHEUS_TARGETS,
    inspect_monitoring,
    validate,
)


def test_monitoring_config_contains_prometheus_targets_and_dashboard() -> None:
    report = inspect_monitoring(Path("."))

    assert REQUIRED_PROMETHEUS_TARGETS.issubset(report["targets"])
    assert all(report["files"].values())
    assert report["dashboard_title"] == "Market Intelligence Overview"
    assert report["dashboard_panels"] >= 2


def test_monitoring_config_validation_passes() -> None:
    assert validate(Path(".")) == []
