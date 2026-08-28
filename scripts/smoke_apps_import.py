import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in ("backend", "backend/common", "ai-engine", "data-platform"):
    sys.path.insert(0, str(ROOT / path))

APP_MODULES = [
    "services.market_service.app.main",
    "services.api_gateway.app.main",
    "services.auth_service.app.main",
    "services.feature_store_service.app.main",
    "services.feature_service.app.main",
    "services.ranking_service.app.main",
    "services.rule_service.app.main",
    "services.score_service.app.main",
    "services.signal_service.app.main",
    "services.alert_service.app.main",
    "services.screener_service.app.main",
    "services.history_service.app.main",
    "services.websocket_service.app.main",
    "ai_engine.app.main",
    "data_platform.app.main",
    "services.notification_service.app.main",
    "services.user_service.app.main",
]


def main() -> None:
    for module_name in APP_MODULES:
        module = importlib.import_module(module_name)
        print(module.app.title)


if __name__ == "__main__":
    main()
