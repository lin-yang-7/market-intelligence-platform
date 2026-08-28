from pathlib import Path

from scripts.validate_cd_workflow import REQUIRED_TOKENS, inspect_cd_workflow, validate


def test_cd_workflow_contains_required_release_steps() -> None:
    report = inspect_cd_workflow(Path(".github/workflows/cd.yml"))

    assert report["exists"] is True
    assert set(REQUIRED_TOKENS).issubset(report["tokens"])
    assert report["has_validate_job"] is True
    assert report["has_package_job"] is True
    assert report["has_deploy_job"] is True


def test_cd_workflow_validation_passes() -> None:
    assert validate() == []
