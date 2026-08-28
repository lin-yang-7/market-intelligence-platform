import argparse
import subprocess
import sys
from pathlib import Path

SECURITY_TEST_FILES = [
    "backend/tests/test_user_api.py",
    "backend/tests/test_api_gateway.py",
    "backend/tests/test_rbac.py",
    "backend/tests/test_signature.py",
    "backend/tests/test_rate_limit.py",
    "backend/tests/test_audit.py",
    "backend/tests/test_secrets.py",
]

REQUIRED_SENSITIVE_ENV_NAMES = {
    "API_KEYS",
    "CLICKHOUSE_PASSWORD",
    "NOTIFICATION_WEBHOOK_URL",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "SMTP_PASSWORD",
    "JWT_SECRET",
}


def static_validate(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in SECURITY_TEST_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing security test file: {relative}")

    required_docs = [
        "docs/10-Testing/06-Security-Test.md",
        "docs/generated/SECRET-ENCRYPTION-MVP-RUNBOOK.md",
    ]
    for relative in required_docs:
        if not (root / relative).is_file():
            errors.append(f"missing security document: {relative}")

    config = (root / "backend/common/mip_common/config.py").read_text(encoding="utf-8")
    for name in sorted(REQUIRED_SENSITIVE_ENV_NAMES):
        if f'"{name}"' not in config:
            errors.append(f"missing sensitive env registration: {name}")

    env_example = (root / ".env.example").read_text(encoding="utf-8")
    if "SECRET_ENCRYPTION_KEY=" not in env_example:
        errors.append("missing SECRET_ENCRYPTION_KEY in .env.example")

    secret_runbook = (root / "docs/generated/SECRET-ENCRYPTION-MVP-RUNBOOK.md").read_text(
        encoding="utf-8"
    )
    if "enc:v1" not in secret_runbook:
        errors.append("secret encryption runbook does not document encrypted value format")
    return errors


def run_pytest(root: Path, extra_args: list[str]) -> int:
    command = [sys.executable, "-m", "pytest", *SECURITY_TEST_FILES, *extra_args]
    return subprocess.run(command, cwd=root, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MVP security test suite.")
    parser.add_argument(
        "--static-only",
        action="store_true",
        help="Only validate security test assets and configuration coverage.",
    )
    parser.add_argument("pytest_args", nargs="*", help="Extra arguments passed to pytest.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    errors = static_validate(root)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("ok: security static checks passed")

    if args.static_only:
        return 0
    return run_pytest(root, args.pytest_args)


if __name__ == "__main__":
    raise SystemExit(main())
