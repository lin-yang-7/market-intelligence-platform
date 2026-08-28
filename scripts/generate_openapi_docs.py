import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in ("backend", "backend/common", "ai-engine", "data-platform"):
    sys.path.insert(0, str(ROOT / path))

APP_MODULES = {
    "api-gateway": "services.api_gateway.app.main",
    "market-service": "services.market_service.app.main",
    "feature-service": "services.feature_service.app.main",
    "feature-store-service": "services.feature_store_service.app.main",
    "ranking-service": "services.ranking_service.app.main",
    "score-service": "services.score_service.app.main",
    "rule-service": "services.rule_service.app.main",
    "signal-service": "services.signal_service.app.main",
    "screener-service": "services.screener_service.app.main",
    "alert-service": "services.alert_service.app.main",
    "history-service": "services.history_service.app.main",
    "websocket-service": "services.websocket_service.app.main",
    "notification-service": "services.notification_service.app.main",
    "user-service": "services.user_service.app.main",
    "ai-engine": "ai_engine.app.main",
    "data-platform": "data_platform.app.main",
}


def main() -> None:
    output_dir = ROOT / "docs" / "generated" / "openapi"
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for service_name, module_name in APP_MODULES.items():
        module = importlib.import_module(module_name)
        schema = module.app.openapi()
        output_path = output_dir / f"{service_name}.openapi.json"
        output_path.write_text(
            json.dumps(schema, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        rows.append((service_name, module.app.title, f"openapi/{output_path.name}"))
    index = ROOT / "docs" / "generated" / "API-INDEX.md"
    lines = [
        "# Generated API Index",
        "",
        "Generated from FastAPI OpenAPI schemas.",
        "",
        "| Service | Title | Schema |",
        "| --- | --- | --- |",
    ]
    lines.extend(f"| {name} | {title} | [{path}]({path}) |" for name, title, path in rows)
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated {len(rows)} OpenAPI schemas in {output_dir}")


if __name__ == "__main__":
    main()
