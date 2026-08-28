import os
from dataclasses import dataclass
from functools import lru_cache

from .secrets import decrypt_secret

SENSITIVE_ENV_NAMES = {
    "API_KEYS",
    "CLICKHOUSE_PASSWORD",
    "NOTIFICATION_WEBHOOK_URL",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "SMTP_PASSWORD",
    "JWT_SECRET",
}


def _getenv(name: str, default: str) -> str:
    value = os.getenv(name, default)
    if name in SENSITIVE_ENV_NAMES and value:
        return decrypt_secret(value)
    return value


def _getenv_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    app_env: str = "local"
    log_level: str = "INFO"
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_market_ticker: str = "market.ticker"
    kafka_topic_market_funding: str = "market.funding"
    kafka_topic_market_open_interest: str = "market.open_interest"
    kafka_topic_market_liquidation: str = "market.liquidation"
    kafka_topic_feature_updated: str = "feature.updated"
    supported_exchanges: str = "binance,bybit,okx,mock"
    collector_exchange: str = "binance"
    collector_symbols: str = "BTCUSDT,ETHUSDT"
    collector_interval_seconds: int = 5
    collector_auto_top_symbols: int = 0
    collector_derivatives_top_symbols: int = 0
    collector_derivatives_interval_seconds: int = 60
    collector_derivative_request_delay_seconds: float = 0.1
    historical_backfill_enabled: bool = False
    historical_backfill_hour_utc: int = 2
    historical_backfill_days: int = 2
    historical_backfill_interval: str = "1h"
    historical_backfill_poll_seconds: int = 60
    api_keys: str = ""
    anonymous_rate_limit_per_minute: int = 100
    api_key_rate_limit_per_minute: int = 1000
    repository_backend: str = "memory"
    clickhouse_url: str = "http://localhost:8123"
    clickhouse_database: str = "market_intelligence"
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    ai_service_url: str = "http://localhost:8010"
    ranking_service_url: str = "http://localhost:8004"
    score_service_url: str = "http://localhost:8014"
    score_service_enabled: bool = False
    ai_scoring_enabled: bool = False
    data_platform_storage_backend: str = "memory"
    data_platform_url: str = "http://localhost:8011"
    data_platform_kafka_topics: str = (
        "market.ticker,market.kline,market.trade,market.funding,market.open_interest,"
        "market.liquidation,feature.updated,ranking.updated,"
        "ranking.entered,ranking.exited,ranking.moved,signal.created"
    )
    data_platform_kafka_group_id: str = "data-platform"
    notification_webhook_url: str = ""
    notification_service_url: str = "http://localhost:8012"
    websocket_service_url: str = "http://localhost:8008"
    ranking_monitor_enabled: bool = True
    ranking_monitor_exchange: str = "binance"
    ranking_monitor_types: str = "abnormalBullish,opportunityBullish,riskBearish"
    ranking_monitor_interval_seconds: int = 60
    ranking_monitor_limit: int = 50
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_email_from: str = ""
    jwt_secret: str = "dev-secret-change-me"
    internal_service_token: str = "local-internal-service-token"
    access_token_ttl_seconds: int = 3600
    admin_emails: str = ""

    def __post_init__(self) -> None:
        insecure_secrets = {
            "",
            "dev-secret-change-me",
            "change-me",
            "REPLACE_WITH_STRONG_SECRET",
        }
        if (
            self.app_env.lower() in {"production", "prod", "staging"}
            and self.jwt_secret in insecure_secrets
        ):
            raise ValueError(
                "JWT_SECRET must be a non-default, non-empty value outside local development"
            )
        insecure_internal_tokens = insecure_secrets | {"local-internal-service-token"}
        if (
            self.app_env.lower() in {"production", "prod", "staging"}
            and self.internal_service_token in insecure_internal_tokens
        ):
            raise ValueError(
                "INTERNAL_SERVICE_TOKEN must be a non-default value outside local development"
            )

    @property
    def collector_symbol_list(self) -> list[str]:
        return [
            symbol.strip().upper()
            for symbol in self.collector_symbols.split(",")
            if symbol.strip()
        ]

    @property
    def supported_exchange_set(self) -> set[str]:
        return {
            exchange.strip().lower()
            for exchange in self.supported_exchanges.split(",")
            if exchange.strip()
        }

    @property
    def api_key_set(self) -> set[str]:
        return {api_key.strip() for api_key in self.api_keys.split(",") if api_key.strip()}

    @property
    def admin_email_set(self) -> set[str]:
        return {email.strip().lower() for email in self.admin_emails.split(",") if email.strip()}

    @property
    def data_platform_topic_list(self) -> list[str]:
        return [
            topic.strip()
            for topic in self.data_platform_kafka_topics.split(",")
            if topic.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_env=_getenv("APP_ENV", "local"),
        log_level=_getenv("LOG_LEVEL", "INFO"),
        redis_url=_getenv("REDIS_URL", "redis://localhost:6379/0"),
        kafka_bootstrap_servers=_getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        kafka_topic_market_ticker=_getenv("KAFKA_TOPIC_MARKET_TICKER", "market.ticker"),
        kafka_topic_market_funding=_getenv("KAFKA_TOPIC_MARKET_FUNDING", "market.funding"),
        kafka_topic_market_open_interest=_getenv(
            "KAFKA_TOPIC_MARKET_OPEN_INTEREST",
            "market.open_interest",
        ),
        kafka_topic_market_liquidation=_getenv(
            "KAFKA_TOPIC_MARKET_LIQUIDATION",
            "market.liquidation",
        ),
        kafka_topic_feature_updated=_getenv("KAFKA_TOPIC_FEATURE_UPDATED", "feature.updated"),
        supported_exchanges=_getenv("SUPPORTED_EXCHANGES", "binance,bybit,okx,mock"),
        collector_exchange=_getenv("COLLECTOR_EXCHANGE", "binance"),
        collector_symbols=_getenv("COLLECTOR_SYMBOLS", "BTCUSDT,ETHUSDT"),
        collector_interval_seconds=_getenv_int("COLLECTOR_INTERVAL_SECONDS", 5),
        collector_auto_top_symbols=_getenv_int("COLLECTOR_AUTO_TOP_SYMBOLS", 0),
        collector_derivatives_top_symbols=_getenv_int("COLLECTOR_DERIVATIVES_TOP_SYMBOLS", 0),
        collector_derivatives_interval_seconds=_getenv_int(
            "COLLECTOR_DERIVATIVES_INTERVAL_SECONDS", 60
        ),
        collector_derivative_request_delay_seconds=float(
            _getenv("COLLECTOR_DERIVATIVE_REQUEST_DELAY_SECONDS", "0.1")
        ),
        historical_backfill_enabled=_getenv("HISTORICAL_BACKFILL_ENABLED", "false").lower()
        == "true",
        historical_backfill_hour_utc=_getenv_int("HISTORICAL_BACKFILL_HOUR_UTC", 2),
        historical_backfill_days=_getenv_int("HISTORICAL_BACKFILL_DAYS", 2),
        historical_backfill_interval=_getenv("HISTORICAL_BACKFILL_INTERVAL", "1h"),
        historical_backfill_poll_seconds=_getenv_int("HISTORICAL_BACKFILL_POLL_SECONDS", 60),
        api_keys=_getenv("API_KEYS", ""),
        anonymous_rate_limit_per_minute=_getenv_int("ANONYMOUS_RATE_LIMIT_PER_MINUTE", 100),
        api_key_rate_limit_per_minute=_getenv_int("API_KEY_RATE_LIMIT_PER_MINUTE", 1000),
        repository_backend=_getenv("REPOSITORY_BACKEND", "memory"),
        clickhouse_url=_getenv("CLICKHOUSE_URL", "http://localhost:8123"),
        clickhouse_database=_getenv("CLICKHOUSE_DATABASE", "market_intelligence"),
        clickhouse_user=_getenv("CLICKHOUSE_USER", "default"),
        clickhouse_password=_getenv("CLICKHOUSE_PASSWORD", ""),
        ai_service_url=_getenv("AI_SERVICE_URL", "http://localhost:8010"),
        ranking_service_url=_getenv("RANKING_SERVICE_URL", "http://localhost:8004"),
        score_service_url=_getenv("SCORE_SERVICE_URL", "http://localhost:8014"),
        score_service_enabled=_getenv("SCORE_SERVICE_ENABLED", "false").lower() == "true",
        ai_scoring_enabled=_getenv("AI_SCORING_ENABLED", "false").lower() == "true",
        data_platform_storage_backend=_getenv("DATA_PLATFORM_STORAGE_BACKEND", "memory"),
        data_platform_url=_getenv("DATA_PLATFORM_URL", "http://localhost:8011"),
        data_platform_kafka_topics=_getenv(
            "DATA_PLATFORM_KAFKA_TOPICS",
            "market.ticker,market.kline,market.trade,market.funding,market.open_interest,"
            "market.liquidation,feature.updated,ranking.updated,"
            "ranking.entered,ranking.exited,ranking.moved,signal.created",
        ),
        data_platform_kafka_group_id=_getenv("DATA_PLATFORM_KAFKA_GROUP_ID", "data-platform"),
        notification_webhook_url=_getenv("NOTIFICATION_WEBHOOK_URL", ""),
        notification_service_url=_getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8012"),
        websocket_service_url=_getenv("WEBSOCKET_SERVICE_URL", "http://localhost:8008"),
        ranking_monitor_enabled=_getenv("RANKING_MONITOR_ENABLED", "true").lower() == "true",
        ranking_monitor_exchange=_getenv("RANKING_MONITOR_EXCHANGE", "binance"),
        ranking_monitor_types=_getenv(
            "RANKING_MONITOR_TYPES",
            "abnormalBullish,opportunityBullish,riskBearish",
        ),
        ranking_monitor_interval_seconds=_getenv_int("RANKING_MONITOR_INTERVAL_SECONDS", 60),
        ranking_monitor_limit=_getenv_int("RANKING_MONITOR_LIMIT", 50),
        telegram_bot_token=_getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=_getenv("TELEGRAM_CHAT_ID", ""),
        smtp_host=_getenv("SMTP_HOST", ""),
        smtp_port=_getenv_int("SMTP_PORT", 587),
        smtp_user=_getenv("SMTP_USER", ""),
        smtp_password=_getenv("SMTP_PASSWORD", ""),
        notification_email_from=_getenv("NOTIFICATION_EMAIL_FROM", ""),
        jwt_secret=_getenv("JWT_SECRET", "dev-secret-change-me"),
        internal_service_token=_getenv(
            "INTERNAL_SERVICE_TOKEN", "local-internal-service-token"
        ),
        access_token_ttl_seconds=_getenv_int("ACCESS_TOKEN_TTL_SECONDS", 3600),
        admin_emails=_getenv("ADMIN_EMAILS", ""),
    )
