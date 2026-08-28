from pathlib import Path

from scripts.validate_k8s_manifests import (
    REQUIRED_DEPLOYMENTS,
    REQUIRED_KINDS,
    inspect_manifest,
    validate,
)


def test_k8s_manifest_contains_required_resources() -> None:
    report = inspect_manifest(Path("deployment/k8s/base.yaml"))

    assert REQUIRED_KINDS.issubset(report["kinds"])
    assert REQUIRED_DEPLOYMENTS.issubset(report["deployments"])
    assert report["has_readiness"] is True
    assert report["has_liveness"] is True
    assert report["has_resources"] is True


def test_k8s_manifest_validation_passes() -> None:
    assert validate(Path("deployment/k8s/base.yaml")) == []
