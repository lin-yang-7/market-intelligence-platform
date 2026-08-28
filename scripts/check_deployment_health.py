import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_SERVICES = {
    "api-gateway": "http://localhost:8000",
    "market-service": "http://localhost:8001",
    "auth-service": "http://localhost:8002",
    "feature-service": "http://localhost:8003",
    "ranking-service": "http://localhost:8004",
    "signal-service": "http://localhost:8005",
    "alert-service": "http://localhost:8006",
    "screener-service": "http://localhost:8007",
    "websocket-service": "http://localhost:8008",
    "history-service": "http://localhost:8009",
    "ai-engine": "http://localhost:8010",
    "data-platform": "http://localhost:8011",
    "notification-service": "http://localhost:8012",
    "user-service": "http://localhost:8013",
    "score-service": "http://localhost:8014",
    "rule-service": "http://localhost:8015",
    "feature-store-service": "http://localhost:8016",
}


def request_json(url: str, timeout: float) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def request_text(url: str, timeout: float) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check service health/readiness/metrics endpoints."
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="Override all services with one API base URL.",
    )
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--service", action="append", help="Limit check to a service name.")
    args = parser.parse_args()

    services = DEFAULT_SERVICES
    if args.service:
        services = {name: DEFAULT_SERVICES[name] for name in args.service}
    if args.base_url:
        services = {"api-gateway": args.base_url.rstrip("/")}

    failed = False
    for name, base_url in services.items():
        try:
            health = request_json(f"{base_url}/health", args.timeout)
            ready = request_json(f"{base_url}/ready", args.timeout)
            metrics = request_text(f"{base_url}/metrics", args.timeout)
            if health.get("status") != "ok" or ready.get("status") != "ready":
                failed = True
                print(f"{name}: not ready health={health} ready={ready}")
                continue
            if "mip_service_up" not in metrics:
                failed = True
                print(f"{name}: metrics missing mip_service_up")
                continue
            print(f"{name}: ok")
        except (KeyError, TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
            failed = True
            print(f"{name}: failed {exc}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
