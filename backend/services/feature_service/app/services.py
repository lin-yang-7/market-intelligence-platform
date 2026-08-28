from mip_common.events import MarketEvent
from mip_common.responses import ServiceError

from .definitions import FEATURE_DEFINITIONS
from .repositories import FeatureRepository
from .schemas import (
    FeatureBatchResponse,
    FeatureDefinition,
    FeatureValue,
    PressureSupportInterpretation,
)


class FeatureService:
    def __init__(self, repository: FeatureRepository) -> None:
        self.repository = repository

    def list_definitions(self) -> list[FeatureDefinition]:
        return list(FEATURE_DEFINITIONS.values())

    def get_definition(self, feature: str) -> FeatureDefinition:
        definition = FEATURE_DEFINITIONS.get(feature.lower())
        if definition is None:
            raise ServiceError(3001, "Feature not found")
        return definition

    async def get_current_feature(
        self,
        symbol: str,
        feature: str,
        exchange: str | None = None,
    ) -> FeatureValue:
        self.get_definition(feature)
        value = await self.repository.get_feature(symbol, feature, exchange)
        if value is None:
            raise ServiceError(3003, "Feature unavailable")
        return value

    async def get_batch(
        self,
        symbol: str,
        features: list[str],
        exchange: str | None = None,
    ) -> FeatureBatchResponse:
        values = [
            await self.get_current_feature(symbol, feature, exchange)
            for feature in features
        ]
        latest_timestamp = max(value.timestamp for value in values)
        first = values[0]
        return FeatureBatchResponse(
            symbol=first.symbol,
            exchange=first.exchange,
            features={value.feature: value.value for value in values},
            timestamp=latest_timestamp,
        )

    async def pressure_support(
        self,
        symbol: str,
        exchange: str | None = None,
    ) -> PressureSupportInterpretation:
        batch = await self.get_batch(
            symbol=symbol,
            exchange=exchange,
            features=[
                "last_price",
                "support_level",
                "resistance_level",
                "main_force_net_inflow",
                "main_force_ratio",
            ],
        )
        derivatives = await self._optional_batch(
            symbol=symbol,
            exchange=exchange,
            features=[
                "funding_pressure",
                "open_interest_change",
                "liquidation_pressure",
                "taker_buy_sell_imbalance",
            ],
        )
        price = batch.features["last_price"]
        support = batch.features["support_level"]
        resistance = batch.features["resistance_level"]
        net_inflow = batch.features["main_force_net_inflow"]
        ratio = batch.features["main_force_ratio"]
        derivative_bias = self._derivative_bias(derivatives)
        if net_inflow > 0 and derivative_bias != "pressure":
            bias = "supportive"
            guidance = (
                "Main-force net inflow is positive; use the support level as the defensive "
                "zone and watch for resistance breakout confirmation."
            )
        elif net_inflow < 0 or derivative_bias == "pressure":
            bias = "pressure"
            guidance = (
                "Main-force net inflow is negative; resistance is the pressure zone and "
                "breaks below support should be treated as risk-off."
            )
        else:
            bias = "neutral"
            guidance = "Main-force flow is neutral; wait for support or resistance confirmation."
        return PressureSupportInterpretation(
            symbol=batch.symbol,
            exchange=batch.exchange,
            price=round(price, 8),
            supportLevel=round(support, 8),
            resistanceLevel=round(resistance, 8),
            mainForceNetInflow=round(net_inflow, 4),
            mainForceRatio=round(ratio, 4),
            bias=bias,
            guidance=guidance,
            timestamp=batch.timestamp,
        )

    async def calculate_from_derivatives(
        self,
        symbol: str,
        exchange: str,
        timestamp: int,
        funding_rate: float | None = None,
        open_interest_change: float | None = None,
        long_liquidation_value: float = 0.0,
        short_liquidation_value: float = 0.0,
        taker_buy_value: float = 0.0,
        taker_sell_value: float = 0.0,
    ) -> list[FeatureValue]:
        values = []
        if funding_rate is not None:
            values.append(
                FeatureValue(
                    symbol=symbol.upper(),
                    exchange=exchange.lower(),
                    feature="funding_pressure",
                    value=max(-100.0, min(100.0, funding_rate * 100_000)),
                    timestamp=timestamp,
                )
            )
        if open_interest_change is not None:
            values.append(
                FeatureValue(
                    symbol=symbol.upper(),
                    exchange=exchange.lower(),
                    feature="open_interest_change",
                    value=max(-100.0, min(100.0, open_interest_change)),
                    timestamp=timestamp,
                )
            )
        total_liquidation = long_liquidation_value + short_liquidation_value
        if total_liquidation > 0:
            values.append(
                FeatureValue(
                    symbol=symbol.upper(),
                    exchange=exchange.lower(),
                    feature="liquidation_pressure",
                    value=((long_liquidation_value - short_liquidation_value) / total_liquidation)
                    * 100,
                    timestamp=timestamp,
                )
            )
        total_taker = taker_buy_value + taker_sell_value
        if total_taker > 0:
            values.append(
                FeatureValue(
                    symbol=symbol.upper(),
                    exchange=exchange.lower(),
                    feature="taker_buy_sell_imbalance",
                    value=((taker_buy_value - taker_sell_value) / total_taker) * 100,
                    timestamp=timestamp,
                )
            )
        await self.repository.save_features(values)
        return values

    async def calculate_from_market_event(self, event: MarketEvent) -> list[FeatureValue]:
        if event.event == "market.ticker":
            return await self.calculate_from_market_ticker(event)
        symbol = str(event.data["symbol"]).upper()
        exchange = event.exchange.lower()
        if event.event == "market.funding":
            return await self.calculate_from_derivatives(
                symbol=symbol,
                exchange=exchange,
                timestamp=event.timestamp,
                funding_rate=float(event.data.get("fundingRate") or 0.0),
            )
        if event.event == "market.open_interest":
            return await self.calculate_from_derivatives(
                symbol=symbol,
                exchange=exchange,
                timestamp=event.timestamp,
                open_interest_change=float(event.data.get("changeRate") or 0.0),
            )
        if event.event == "market.liquidation":
            value = float(event.data.get("value") or 0.0)
            side = str(event.data.get("side", "")).lower()
            return await self.calculate_from_derivatives(
                symbol=symbol,
                exchange=exchange,
                timestamp=event.timestamp,
                long_liquidation_value=value if side == "long" else 0.0,
                short_liquidation_value=value if side == "short" else 0.0,
            )
        if event.event == "market.trade":
            value = float(event.data.get("price") or 0.0) * float(event.data.get("quantity") or 0.0)
            side = str(event.data.get("side", "")).lower()
            return await self.calculate_from_derivatives(
                symbol=symbol,
                exchange=exchange,
                timestamp=event.timestamp,
                taker_buy_value=value if side == "buy" else 0.0,
                taker_sell_value=value if side == "sell" else 0.0,
            )
        raise ServiceError(2001, "Invalid event type")

    async def get_history(
        self,
        symbol: str,
        feature: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[FeatureValue]:
        self.get_definition(feature)
        self._validate_time_range(start_time, end_time)
        values = await self.repository.list_history(
            symbol=symbol,
            feature=feature,
            exchange=exchange,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        if not values:
            raise ServiceError(3003, "Feature unavailable")
        return values

    async def calculate_from_market_ticker(self, event: MarketEvent) -> list[FeatureValue]:
        if event.event != "market.ticker":
            raise ServiceError(2001, "Invalid event type")

        symbol = str(event.data["symbol"]).upper()
        price = float(event.data.get("price") or 0.0)
        price_change = float(event.data.get("change24h") or 0.0)
        volume = float(event.data.get("volume24h") or 0.0)
        volume_activity = min(100.0, max(0.0, volume / 1_000_000.0))
        price_momentum = max(-100.0, min(100.0, price_change))
        positive_momentum = max(0.0, price_momentum)
        long_inflow_score = min(100.0, positive_momentum * 10.0 + volume_activity * 0.3)
        main_force_net_inflow = volume * ((long_inflow_score - 50.0) / 100.0)
        main_force_ratio = self._main_force_ratio(long_inflow_score)
        support_level, resistance_level = self._pressure_support_levels(
            price,
            main_force_net_inflow,
            main_force_ratio,
        )

        values = [
            FeatureValue(
                symbol=symbol,
                exchange=event.exchange.lower(),
                feature="last_price",
                value=price,
                timestamp=event.timestamp,
            ),
            FeatureValue(
                symbol=symbol,
                exchange=event.exchange.lower(),
                feature="price_momentum",
                value=price_momentum,
                timestamp=event.timestamp,
            ),
            FeatureValue(
                symbol=symbol,
                exchange=event.exchange.lower(),
                feature="volume_activity",
                value=volume_activity,
                timestamp=event.timestamp,
            ),
            FeatureValue(
                symbol=symbol,
                exchange=event.exchange.lower(),
                feature="long_inflow_score",
                value=long_inflow_score,
                timestamp=event.timestamp,
            ),
            FeatureValue(
                symbol=symbol,
                exchange=event.exchange.lower(),
                feature="main_force_net_inflow",
                value=main_force_net_inflow,
                timestamp=event.timestamp,
            ),
            FeatureValue(
                symbol=symbol,
                exchange=event.exchange.lower(),
                feature="main_force_ratio",
                value=main_force_ratio,
                timestamp=event.timestamp,
            ),
            FeatureValue(
                symbol=symbol,
                exchange=event.exchange.lower(),
                feature="support_level",
                value=support_level,
                timestamp=event.timestamp,
            ),
            FeatureValue(
                symbol=symbol,
                exchange=event.exchange.lower(),
                feature="resistance_level",
                value=resistance_level,
                timestamp=event.timestamp,
            ),
        ]
        await self.repository.save_features(values)
        return values

    @staticmethod
    def _main_force_ratio(long_inflow_score: float) -> float:
        strength = min(1.0, abs(long_inflow_score - 50.0) / 50.0)
        return 20.0 + strength * 10.0

    @staticmethod
    def _pressure_support_levels(
        price: float,
        main_force_net_inflow: float,
        main_force_ratio: float,
    ) -> tuple[float, float]:
        ratio = main_force_ratio / 100.0
        if main_force_net_inflow >= 0:
            return price * (1 - ratio), price * (1 + ratio * 0.5)
        return price * (1 - ratio * 0.5), price * (1 + ratio)

    async def _optional_batch(
        self,
        symbol: str,
        exchange: str | None,
        features: list[str],
    ) -> dict[str, float]:
        values = {}
        for feature in features:
            try:
                value = await self.get_current_feature(symbol, feature, exchange)
                values[feature] = value.value
            except ServiceError:
                continue
        return values

    @staticmethod
    def _derivative_bias(features: dict[str, float]) -> str:
        pressure = 0.0
        pressure += max(0.0, features.get("funding_pressure", 0.0)) * 0.25
        pressure += max(0.0, features.get("open_interest_change", 0.0)) * 0.20
        pressure += max(0.0, features.get("liquidation_pressure", 0.0)) * 0.30
        pressure += max(0.0, -features.get("taker_buy_sell_imbalance", 0.0)) * 0.25
        support = max(0.0, features.get("taker_buy_sell_imbalance", 0.0)) * 0.4
        support += max(0.0, -features.get("liquidation_pressure", 0.0)) * 0.3
        if pressure >= 35 and pressure > support:
            return "pressure"
        if support >= 35 and support > pressure:
            return "supportive"
        return "neutral"

    @staticmethod
    def _validate_time_range(start_time: int | None, end_time: int | None) -> None:
        if start_time is not None and start_time < 0:
            raise ServiceError(2003, "Invalid time range")
        if end_time is not None and end_time < 0:
            raise ServiceError(2003, "Invalid time range")
        if start_time is not None and end_time is not None and start_time > end_time:
            raise ServiceError(2003, "Invalid time range")
