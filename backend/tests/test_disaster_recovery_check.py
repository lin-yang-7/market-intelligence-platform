from pathlib import Path

from scripts.disaster_recovery_check import REQUIRED_ARTIFACTS, inspect_artifacts, render_report


def test_disaster_recovery_required_artifacts_exist() -> None:
    artifacts = inspect_artifacts(Path("."))

    assert set(artifacts) == set(REQUIRED_ARTIFACTS)
    assert all(artifacts.values())


def test_disaster_recovery_report_contains_recovery_checks() -> None:
    report = render_report(Path("."))

    assert "Disaster Recovery Readiness Check" in report
    assert "Restore MySQL baseline" in report
    assert "Verify ranking monitor historical event query" in report
    assert report.endswith("ready")
