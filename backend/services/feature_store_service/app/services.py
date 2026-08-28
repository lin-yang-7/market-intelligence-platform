import hashlib

from mip_common.models import model_copy_with_update
from mip_common.responses import ServiceError, now_ms
from services.feature_service.app.definitions import FEATURE_DEFINITIONS

from .repositories import FeatureStoreRepository
from .schemas import (
    FeatureDefinitionRecord,
    FeatureDefinitionRequest,
    FeatureValueRecord,
    FeatureValueWrite,
    MaterializedFeatureSet,
)


class FeatureStoreService:
    def __init__(self, repository: FeatureStoreRepository) -> None:
        self.repository = repository

    async def bootstrap_defaults(self) -> None:
        existing = await self.repository.list_definitions()
        if existing:
            return
        for definition in FEATURE_DEFINITIONS.values():
            await self.register(
                FeatureDefinitionRequest(
                    name=definition.name,
                    category=definition.category,
                    version=definition.version,
                    description=definition.description,
                    formula="managed by feature-service",
                    dataSource="market.ticker",
                    updateFrequency=definition.updateInterval,
                    owner="system",
                )
            )

    async def register(self, request: FeatureDefinitionRequest) -> FeatureDefinitionRecord:
        timestamp = now_ms()
        existing = await self.repository.get_definition(request.name, request.version)
        feature_id = (
            existing.featureId
            if existing
            else self._id("feat", request.name, request.version)
        )
        record = FeatureDefinitionRecord(
            featureId=feature_id,
            name=request.name.lower(),
            category=request.category,
            version=request.version,
            description=request.description,
            formula=request.formula,
            dataSource=request.dataSource,
            updateFrequency=request.updateFrequency,
            owner=request.owner,
            dependencies=request.dependencies,
            status="active",
            createdAt=existing.createdAt if existing else timestamp,
            updatedAt=timestamp,
        )
        await self.repository.save_definition(record)
        return record

    async def list_definitions(
        self,
        category: str | None = None,
        status: str | None = "active",
    ) -> list[FeatureDefinitionRecord]:
        await self.bootstrap_defaults()
        return await self.repository.list_definitions(category=category, status=status)

    async def get_definition(
        self,
        name: str,
        version: str | None = None,
    ) -> FeatureDefinitionRecord:
        await self.bootstrap_defaults()
        definition = await self.repository.get_definition(name, version)
        if definition is None:
            raise ServiceError(7201, "Feature definition not found")
        return definition

    async def write_value(self, request: FeatureValueWrite) -> FeatureValueRecord:
        definition = await self.repository.get_definition(request.feature, request.version)
        if definition is None:
            definition = await self.register(
                FeatureDefinitionRequest(
                    name=request.feature,
                    category="custom",
                    version=request.version,
                    description="auto-registered feature",
                )
            )
        record = FeatureValueRecord(
            featureId=definition.featureId,
            symbol=request.symbol.upper(),
            exchange=request.exchange.lower(),
            feature=request.feature.lower(),
            value=request.value,
            version=request.version,
            timestamp=request.timestamp,
            storedAt=now_ms(),
        )
        await self.repository.save_value(record)
        return record

    async def latest(
        self,
        symbol: str,
        feature: str,
        exchange: str | None = None,
    ) -> FeatureValueRecord:
        value = await self.repository.get_latest(symbol=symbol, feature=feature, exchange=exchange)
        if value is None:
            raise ServiceError(7202, "Feature value unavailable")
        return value

    async def history(
        self,
        symbol: str,
        feature: str,
        exchange: str | None = None,
        limit: int = 100,
    ) -> list[FeatureValueRecord]:
        values = await self.repository.list_history(
            symbol=symbol,
            feature=feature,
            exchange=exchange,
            limit=limit,
        )
        if not values:
            raise ServiceError(7202, "Feature value unavailable")
        return values

    async def materialize(
        self,
        symbol: str,
        features: list[str],
        exchange: str | None = None,
    ) -> MaterializedFeatureSet:
        values = [await self.latest(symbol, feature, exchange) for feature in features]
        first = values[0]
        return MaterializedFeatureSet(
            symbol=first.symbol,
            exchange=first.exchange,
            features={value.feature: value.value for value in values},
            versions={value.feature: value.version for value in values},
            timestamp=max(value.timestamp for value in values),
        )

    async def disable_definition(
        self,
        name: str,
        version: str | None = None,
    ) -> FeatureDefinitionRecord:
        definition = await self.get_definition(name, version)
        updated = model_copy_with_update(
            definition,
            {"status": "disabled", "updatedAt": now_ms()},
        )
        await self.repository.save_definition(updated)
        return updated

    @staticmethod
    def _id(prefix: str, *parts: object) -> str:
        raw = ":".join(str(part) for part in parts).encode()
        digest = hashlib.sha1(raw).hexdigest()[:12]
        return f"{prefix}_{digest}"
