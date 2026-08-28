from time import perf_counter
from typing import Any

from fastapi import FastAPI, Response

from .responses import now_ms


def install_ops_routes(
    app: FastAPI,
    service_name: str,
    readiness_checks: dict[str, Any] | None = None,
) -> None:
    started_at = perf_counter()

    @app.get("/ready")
    async def ready() -> dict[str, Any]:
        checks = {}
        for name, check in (readiness_checks or {}).items():
            result = check()
            if hasattr(result, "__await__"):
                result = await result
            checks[name] = bool(result)
        ready_state = all(checks.values()) if checks else True
        return {
            "status": "ready" if ready_state else "not_ready",
            "service": service_name,
            "checks": checks,
            "serverTime": now_ms(),
        }

    @app.get("/metrics")
    async def metrics() -> Response:
        uptime_seconds = perf_counter() - started_at
        body = "\n".join(
            [
                "# HELP mip_service_up Service process is running.",
                "# TYPE mip_service_up gauge",
                f'mip_service_up{{service="{service_name}"}} 1',
                "# HELP mip_service_uptime_seconds Service process uptime in seconds.",
                "# TYPE mip_service_uptime_seconds gauge",
                f'mip_service_uptime_seconds{{service="{service_name}"}} {uptime_seconds:.3f}',
                "",
            ]
        )
        return Response(content=body, media_type="text/plain; version=0.0.4")
