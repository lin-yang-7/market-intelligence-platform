import argparse
from pathlib import Path

REQUIRED_KINDS = {"Namespace", "ConfigMap", "Secret", "Deployment", "Service", "Ingress"}
REQUIRED_DEPLOYMENTS = {
    "api-gateway",
    "market-service",
    "feature-service",
    "ranking-service",
    "websocket-service",
    "history-service",
    "ai-engine",
    "data-platform",
    "ranking-monitor-worker",
}


def split_documents(text: str) -> list[str]:
    return [document.strip() for document in text.split("---") if document.strip()]


def extract_field(document: str, field: str) -> str | None:
    lines = document.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == f"{field}:":
            for nested in lines[index + 1 :]:
                stripped = nested.strip()
                if stripped.startswith("name:"):
                    return stripped.split(":", 1)[1].strip()
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return None


def inspect_manifest(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    documents = split_documents(text)
    kinds = {extract_field(document, "kind") for document in documents}
    deployments = {
        extract_field(document, "metadata")
        for document in documents
        if extract_field(document, "kind") == "Deployment"
    }
    return {
        "documents": len(documents),
        "kinds": {kind for kind in kinds if kind},
        "deployments": {name for name in deployments if name},
        "has_readiness": "/ready" in text,
        "has_liveness": "/health" in text,
        "has_resources": "resources:" in text,
    }


def validate(path: Path) -> list[str]:
    report = inspect_manifest(path)
    issues = []
    missing_kinds = REQUIRED_KINDS - report["kinds"]
    missing_deployments = REQUIRED_DEPLOYMENTS - report["deployments"]
    if missing_kinds:
        issues.append(f"missing kinds: {', '.join(sorted(missing_kinds))}")
    if missing_deployments:
        issues.append(f"missing deployments: {', '.join(sorted(missing_deployments))}")
    if not report["has_readiness"]:
        issues.append("missing readiness probes")
    if not report["has_liveness"]:
        issues.append("missing liveness probes")
    if not report["has_resources"]:
        issues.append("missing resource requests/limits")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Kubernetes MVP manifests.")
    parser.add_argument("--path", default="deployment/k8s/base.yaml")
    args = parser.parse_args()

    path = Path(args.path)
    issues = validate(path)
    if issues:
        for issue in issues:
            print(f"failed: {issue}")
        return 1
    report = inspect_manifest(path)
    print(
        "ok: "
        f"{report['documents']} documents, "
        f"{len(report['deployments'])} deployments, "
        f"{len(report['kinds'])} resource kinds"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
