import operator
from collections.abc import Callable

from mip_common.models import model_copy_with_update
from mip_common.responses import ServiceError
from services.feature_service.app.repositories import FeatureRepository
from services.ranking_service.app.services import RankingService

from .presets import SCREENER_PRESETS
from .schemas import (
    CustomScreenerRequest,
    LongInflowScreenerRequest,
    ScreenerCondition,
    ScreenerPreset,
    ScreenerQueryRequest,
    ScreenerResult,
)

OPERATORS: dict[str, Callable[[float, float], bool]] = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "=": operator.eq,
    "==": operator.eq,
}
RANKING_BY_SCREENER_TYPE = {
    "longInflow": "longInflow",
    "momentum": "momentum",
    "volume": "volume",
}


class ScreenerService:
    def __init__(self, feature_repository: FeatureRepository) -> None:
        self.feature_repository = feature_repository
        self.ranking_service = RankingService(feature_repository)

    def list_presets(self) -> list[ScreenerPreset]:
        return list(SCREENER_PRESETS.values())

    async def query(self, request: ScreenerQueryRequest) -> list[ScreenerResult]:
        if request.type == "custom":
            raise ServiceError(5001, "Invalid condition")
        ranking_type = RANKING_BY_SCREENER_TYPE.get(request.type)
        if ranking_type is None:
            raise ServiceError(5001, "Invalid condition")
        ranking = await self.ranking_service.get_ranking(
            ranking_type,
            exchange=request.exchange,
            limit=request.limit,
        )
        results = [
            self._from_ranking_item(item)
            for item in ranking
            if item.score >= request.minScore
        ]
        return self._require_matches(results)

    async def long_inflow(self, request: LongInflowScreenerRequest) -> list[ScreenerResult]:
        ranking = await self.ranking_service.get_ranking(
            "longInflow",
            exchange=request.exchange,
            limit=request.limit,
        )
        results = [
            self._from_ranking_item(item)
            for item in ranking
            if item.score >= request.minScore
            and item.factors.get("volume_activity", 0.0) >= request.minVolume
        ]
        return self._require_matches(results)

    async def custom(self, request: CustomScreenerRequest) -> list[ScreenerResult]:
        if not request.conditions:
            raise ServiceError(5001, "Invalid condition")
        feature_values = await self.feature_repository.list_features()
        by_symbol: dict[tuple[str, str], dict[str, float]] = {}
        timestamps: dict[tuple[str, str], int] = {}

        for value in feature_values:
            if request.exchange and value.exchange.lower() != request.exchange.lower():
                continue
            key = (value.exchange.lower(), value.symbol.upper())
            by_symbol.setdefault(key, {})[value.feature] = value.value
            timestamps[key] = max(timestamps.get(key, 0), value.timestamp)

        results: list[ScreenerResult] = []
        for (exchange, symbol), factors in by_symbol.items():
            if all(self._matches_condition(factors, condition) for condition in request.conditions):
                score = self._custom_score(factors, request.conditions)
                results.append(
                    ScreenerResult(
                        symbol=symbol,
                        exchange=exchange,
                        score=score,
                        rank=0,
                        signals=self._signals(factors),
                        timestamp=timestamps[(exchange, symbol)],
                        factors=factors,
                    )
                )

        results.sort(key=lambda item: item.score, reverse=True)
        ranked = [
            model_copy_with_update(item, {"rank": index})
            for index, item in enumerate(results[: request.limit], start=1)
        ]
        return self._require_matches(ranked)

    def _matches_condition(self, factors: dict[str, float], condition: ScreenerCondition) -> bool:
        actual = factors.get(condition.feature)
        if actual is None:
            return False
        operator_name = condition.operator
        if operator_name in OPERATORS:
            return OPERATORS[operator_name](actual, float(condition.value))
        if operator_name == "between":
            if not isinstance(condition.value, (list, tuple)) or len(condition.value) != 2:
                raise ServiceError(5001, "Invalid condition")
            low, high = float(condition.value[0]), float(condition.value[1])
            return low <= actual <= high
        if operator_name == "in":
            if not isinstance(condition.value, (list, tuple, set)):
                raise ServiceError(5001, "Invalid condition")
            return actual in {float(value) for value in condition.value}
        raise ServiceError(5001, "Invalid condition")

    def _from_ranking_item(self, item) -> ScreenerResult:
        return ScreenerResult(
            symbol=item.symbol,
            exchange=item.exchange,
            score=item.score,
            rank=item.rank,
            signals=self._signals(item.factors),
            timestamp=item.timestamp,
            factors=item.factors,
        )

    @staticmethod
    def _signals(factors: dict[str, float]) -> list[str]:
        signals: list[str] = []
        if factors.get("long_inflow_score", 0.0) >= 70:
            signals.append("high_inflow")
        if factors.get("volume_activity", 0.0) >= 70:
            signals.append("volume_breakout")
        if factors.get("price_momentum", 0.0) > 0:
            signals.append("positive_momentum")
        return signals

    @staticmethod
    def _custom_score(factors: dict[str, float], conditions: list[ScreenerCondition]) -> float:
        values = [abs(float(factors.get(condition.feature, 0.0))) for condition in conditions]
        if not values:
            return 0.0
        return round(min(100.0, sum(values) / len(values)), 4)

    @staticmethod
    def _require_matches(results: list[ScreenerResult]) -> list[ScreenerResult]:
        if not results:
            raise ServiceError(5003, "No matching coins")
        return results
