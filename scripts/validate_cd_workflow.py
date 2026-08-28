from pathlib import Path

REQUIRED_TOKENS = [
    "workflow_dispatch",
    "environment:",
    "docker/login-action",
    "docker build",
    "docker push",
    "appleboy/ssh-action",
    "DEPLOY_HOST",
    "DEPLOY_USER",
    "DEPLOY_SSH_KEY",
    "DEPLOY_PATH",
    "deployment/docker-compose.prod.yml",
    "check_deployment_health.py",
    "rollback",
]


def inspect_cd_workflow(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return {
        "exists": path.exists(),
        "tokens": {token for token in REQUIRED_TOKENS if token in text},
        "has_validate_job": "validate:" in text and "python scripts/run_ci.py" in text,
        "has_package_job": "package:" in text and "Build and push image" in text,
        "has_deploy_job": "deploy:" in text and "Deploy over SSH" in text,
    }


def validate(path: Path = Path(".github/workflows/cd.yml")) -> list[str]:
    report = inspect_cd_workflow(path)
    issues = []
    if not report["exists"]:
        issues.append("missing CD workflow")
    missing_tokens = set(REQUIRED_TOKENS) - report["tokens"]
    if missing_tokens:
        issues.append(f"missing CD tokens: {', '.join(sorted(missing_tokens))}")
    for key in ("has_validate_job", "has_package_job", "has_deploy_job"):
        if not report[key]:
            issues.append(f"missing {key}")
    return issues


def main() -> int:
    issues = validate()
    if issues:
        for issue in issues:
            print(f"failed: {issue}")
        return 1
    print("ok: CD workflow includes validation, package, deploy, verify, and rollback guidance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
