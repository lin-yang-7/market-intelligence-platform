import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SERVICE_PORTS = {
    "auth-service": 8002,
    "api-gateway": 8000,
}


def static_validate(root: Path, service: str) -> list[str]:
    compose = root / "deployment/docker-compose.yml"
    dockerfile = root / "backend/Dockerfile.service"
    issues = []
    compose_text = compose.read_text(encoding="utf-8") if compose.exists() else ""
    dockerfile_text = dockerfile.read_text(encoding="utf-8") if dockerfile.exists() else ""
    if service not in compose_text:
        issues.append(f"service {service} missing from docker-compose.yml")
    if "backend/Dockerfile.service" not in compose_text:
        issues.append("compose file does not reference backend/Dockerfile.service")
    if "PYTHONPATH" not in dockerfile_text:
        issues.append("Dockerfile missing PYTHONPATH")
    if "requirements.txt" not in dockerfile_text:
        issues.append("Dockerfile missing requirements install")
    return issues


def request_ready(port: int, timeout: float) -> bool:
    url = f"http://localhost:{port}/ready"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload.get("status") == "ready"
    except (TimeoutError, urllib.error.URLError, json.JSONDecodeError):
        return False


def wait_ready(port: int, timeout_seconds: int) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if request_ready(port, timeout=3):
            return True
        time.sleep(2)
    return False


def run_full(root: Path, service: str, timeout_seconds: int) -> int:
    if shutil.which("docker") is None:
        print("failed: docker executable not found")
        return 1
    port = SERVICE_PORTS[service]
    compose = root / "deployment/docker-compose.yml"
    command = ["docker", "compose", "-f", str(compose), "up", "-d", "--build", service]
    try:
        subprocess.run(command, cwd=root, check=True)
        if not wait_ready(port, timeout_seconds):
            print(f"failed: {service} did not become ready on port {port}")
            return 1
        print(f"ok: {service} container is ready")
        return 0
    finally:
        subprocess.run(
            ["docker", "compose", "-f", str(compose), "down", "--remove-orphans"],
            cwd=root,
            check=False,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Docker integration checks.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--service", default="auth-service", choices=sorted(SERVICE_PORTS))
    parser.add_argument("--mode", default="static", choices=["static", "full"])
    parser.add_argument("--timeout-seconds", type=int, default=90)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    issues = static_validate(root, args.service)
    if issues:
        for issue in issues:
            print(f"failed: {issue}")
        return 1
    if args.mode == "static":
        print(f"ok: Docker integration static checks passed for {args.service}")
        return 0
    return run_full(root, args.service, args.timeout_seconds)


if __name__ == "__main__":
    sys.exit(main())
