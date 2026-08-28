from typing import Protocol

from .schemas import FeatureDefinitionRecord, FeatureValueRecord


class FeatureStoreRepository(Protocol):
    async def save_definition(self, definition: FeatureDefinitionRecord) -> None:
        ...

    async def get_definition(
        self,
        name: str,
        version: str | None = None,
    ) -> FeatureDefinitionRecord | None:
        ...

    async def list_definitions(
        self,
        category: str | None = None,
        status: str | None = None,
    ) -> list[FeatureDefinitionRecord]:
        ...

    async def save_value(self, value: FeatureValueRecord) -> None:
        ...

    async def get_latest(
        self,
        symbol: str,
        feature: str,
        exchange: str | None = None,
    ) -> FeatureValueRecord | None:
        ...

    async def list_history(
        self,
        symbol: str,
        feature: str,
        exchange: str | None = None,
        limit: int = 100,
    ) -> list[FeatureValueRecord]:
        ...


class InMemoryFeatureStoreRepository:
    def __init__(self) -> None:
        self._definitions: dict[tuple[str, str], FeatureDefinitionRecord] = {}
        self._latest: dict[tuple[str, str, str], FeatureValueRecord] = {}
        self._history: list[FeatureValueRecord] = []

    async def save_definition(self, definition: FeatureDefinitionRecord) -> None:
        self._definitions[(definition.name.lower(), definition.version)] = definition

    async def get_definition(
        self,
        name: str,
        version: str | None = None,
    ) -> FeatureDefinitionRecord | None:
        name = name.lower()
        if version:
            return self._definitions.get((name, version))
        candidates = [
            definition
            for (feature_name, _version), definition in self._definitions.items()
            if feature_name == name
        ]
        candidates.sort(key=lambda definition: definition.updatedAt, reverse=True)
        return candidates[0] if candidates else None

    async def list_definitions(
        self,
        category: str | None = None,
        status: str | None = None,
    ) -> list[FeatureDefinitionRecord]:
        definitions = list(self._definitions.values())
        if category:
            definitions = [item for item in definitions if item.category == category]
        if status:
            definitions = [item for item in definitions if item.status == status]
        definitions.sort(key=lambda item: (item.name, item.version))
        return definitions

    async def save_value(self, value: FeatureValueRecord) -> None:
        key = (value.exchange.lower(), value.symbol.upper(), value.feature.lower())
        self._latest[key] = value
        self._history.append(value)

    async def get_latest(
        self,
        symbol: str,
        feature: str,
        exchange: str | None = None,
    ) -> FeatureValueRecord | None:
        symbol = symbol.upper()
        feature = feature.lower()
        if exchange:
            return self._latest.get((exchange.lower(), symbol, feature))
        candidates = [
            value
            for (_exchange, value_symbol, value_feature), value in self._latest.items()
            if value_symbol == symbol and value_feature == feature
        ]
        candidates.sort(key=lambda item: item.timestamp, reverse=True)
        return candidates[0] if candidates else None

    async def list_history(
        self,
        symbol: str,
        feature: str,
        exchange: str | None = None,
        limit: int = 100,
    ) -> list[FeatureValueRecord]:
        symbol = symbol.upper()
        feature = feature.lower()
        values = [
            value
            for value in self._history
            if value.symbol == symbol
            and value.feature == feature
            and (exchange is None or value.exchange == exchange.lower())
        ]
        values.sort(key=lambda item: item.timestamp, reverse=True)
        return values[: max(1, min(limit, 1000))]
