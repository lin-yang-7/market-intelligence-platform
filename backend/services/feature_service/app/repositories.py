from typing import Protocol

from mip_common.models import validate_model
from mip_common.redis import (
    redis_get_json_list,
    redis_get_model,
    redis_set_json_list,
    redis_set_model,
)

from .schemas import FeatureValue


class FeatureRepository(Protocol):
    async def list_features(self) -> list[FeatureValue]:
        ...

    async def get_feature(
        self,
        symbol: str,
        feature: str,
        exchange: str | None = None,
    ) -> FeatureValue | None:
        ...

    async def save_features(self, features: list[FeatureValue]) -> None:
        ...

    async def list_history(
        self,
        symbol: str,
        feature: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[FeatureValue]:
        ...


class InMemoryFeatureRepository:
    def __init__(self) -> None:
        self._features: dict[tuple[str, str, str], FeatureValue] = {}
        self._history: list[FeatureValue] = []

    async def list_features(self) -> list[FeatureValue]:
        return list(self._features.values())

    async def get_feature(
        self,
        symbol: str,
        feature: str,
        exchange: str | None = None,
    ) -> FeatureValue | None:
        symbol = symbol.upper()
        feature = feature.lower()
        if exchange:
            return self._features.get((exchange.lower(), symbol, feature))
        candidates = [
            value
            for (_exchange, feature_symbol, feature_name), value in self._features.items()
            if feature_symbol == symbol and feature_name == feature
        ]
        return candidates[0] if candidates else None

    async def save_features(self, features: list[FeatureValue]) -> None:
        for feature in features:
            key = (feature.exchange.lower(), feature.symbol.upper(), feature.feature.lower())
            self._features[key] = feature
            self._history.append(feature)

    async def list_history(
        self,
        symbol: str,
        feature: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[FeatureValue]:
        symbol = symbol.upper()
        feature = feature.lower()
        values = [
            value
            for value in self._history
            if value.symbol == symbol
            and value.feature == feature
            and (exchange is None or value.exchange == exchange.lower())
            and (start_time is None or value.timestamp >= start_time)
            and (end_time is None or value.timestamp <= end_time)
        ]
        values.sort(key=lambda value: value.timestamp, reverse=True)
        return values[: max(1, min(limit, 1000))]


class RedisFeatureRepository:
    def __init__(self, redis_client, ttl_seconds: int = 300) -> None:
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds

    async def list_features(self) -> list[FeatureValue]:
        rows = await redis_get_json_list(self.redis, self._latest_index_key())
        return [validate_model(FeatureValue, row) for row in rows]

    async def get_feature(
        self,
        symbol: str,
        feature: str,
        exchange: str | None = None,
    ) -> FeatureValue | None:
        if exchange:
            return await redis_get_model(
                self.redis,
                self._latest_key(exchange, symbol, feature),
                FeatureValue,
            )
        rows = await self.list_features()
        symbol = symbol.upper()
        feature = feature.lower()
        candidates = [row for row in rows if row.symbol == symbol and row.feature == feature]
        return candidates[0] if candidates else None

    async def save_features(self, features: list[FeatureValue]) -> None:
        latest = {self._identity(feature): feature for feature in await self.list_features()}
        for feature in features:
            latest[self._identity(feature)] = feature
            await redis_set_model(
                self.redis,
                self._latest_key(feature.exchange, feature.symbol, feature.feature),
                feature,
                self.ttl_seconds,
            )
            history = await self._history(feature.symbol, feature.feature, feature.exchange)
            history.append(feature)
            await redis_set_json_list(
                self.redis,
                self._history_key(feature.exchange, feature.symbol, feature.feature),
                history,
            )
        await redis_set_json_list(self.redis, self._latest_index_key(), list(latest.values()))

    async def list_history(
        self,
        symbol: str,
        feature: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[FeatureValue]:
        if exchange:
            values = await self._history(symbol, feature, exchange)
        else:
            values = [
                value
                for value in await self.list_features()
                if value.symbol == symbol.upper() and value.feature == feature.lower()
            ]
        values = [
            value
            for value in values
            if (start_time is None or value.timestamp >= start_time)
            and (end_time is None or value.timestamp <= end_time)
        ]
        values.sort(key=lambda value: value.timestamp, reverse=True)
        return values[: max(1, min(limit, 1000))]

    async def _history(self, symbol: str, feature: str, exchange: str) -> list[FeatureValue]:
        rows = await redis_get_json_list(self.redis, self._history_key(exchange, symbol, feature))
        return [validate_model(FeatureValue, row) for row in rows]

    @staticmethod
    def _identity(feature: FeatureValue) -> tuple[str, str, str]:
        return (feature.exchange.lower(), feature.symbol.upper(), feature.feature.lower())

    @staticmethod
    def _latest_key(exchange: str, symbol: str, feature: str) -> str:
        return f"feature:{exchange.lower()}:{symbol.upper()}:{feature.lower()}"

    @staticmethod
    def _history_key(exchange: str, symbol: str, feature: str) -> str:
        return f"feature:history:{exchange.lower()}:{symbol.upper()}:{feature.lower()}"

    @staticmethod
    def _latest_index_key() -> str:
        return "feature:latest:index"
