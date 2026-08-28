import subprocess
import sys

NPM = "npm.cmd" if sys.platform == "win32" else "npm"

COMMANDS = [
    [
        sys.executable,
        "-m",
        "ruff",
        "check",
        "backend",
        "ai-engine",
        "data-platform",
        "scripts",
        "sdk",
    ],
    [sys.executable, "-m", "pytest"],
    [sys.executable, "scripts/smoke_apps_import.py"],
    [sys.executable, "scripts/disaster_recovery_check.py"],
    [sys.executable, "scripts/validate_k8s_manifests.py"],
    [sys.executable, "scripts/validate_monitoring_config.py"],
    [sys.executable, "scripts/validate_cd_workflow.py"],
    [sys.executable, "scripts/validate_data_platform_full.py"],
    [sys.executable, "scripts/validate_admin_console.py"],
    [sys.executable, "scripts/docker_integration_test.py", "--mode", "static"],
    [sys.executable, "scripts/security_test.py"],
    [NPM, "run", "build", "--prefix", "frontend"],
]


def main() -> int:
    for command in COMMANDS:
        print(f"> {' '.join(command)}", flush=True)
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            return completed.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
