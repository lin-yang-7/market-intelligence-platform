from mip_common.models import model_copy_with_update
from mip_common.responses import ServiceError, now_ms
from services.feature_service.app.repositories import FeatureRepository

from .ai_scorer import AiRankingScorer, DisabledAiRankingScorer
from .schemas import (
    RankingEntered,
    RankingExited,
    RankingItem,
    RankingMonitorChanges,
    RankingMonitorSnapshot,
    RankingMoved,
    RankingStrategyEvent,
)
from .score_client import DisabledRankingScoreClient, RankingScoreClient

RANKING_FEATURES: dict[str, str] = {
    "longInflow": "long_inflow_score",
    "momentum": "price_momentum",
    "volume": "volume_activity",
    "abnormalBullish": "price_momentum",
    "opportunityBullish": "long_inflow_score",
    "riskBearish": "price_momentum",
}
MONITOR_DEFAULT_THRESHOLDS = {
    "abnormalBullish": 55.0,
    "opportunityBullish": 55.0,
    "riskBearish": 55.0,
}
MONITOR_DEFAULT_MAX_SCORES: dict[str, float | None] = {
    "abnormalBullish": None,
    "opportunityBullish": 80.0,
    "riskBearish": None,
}


class RankingService:
    def __init__(
        self,
        feature_repository: FeatureRepository,
        ai_scorer: AiRankingScorer | None = None,
        score_client: RankingScoreClient | None = None,
    ) -> None:
        self.feature_repository = feature_repository
        self.ai_scorer = ai_scorer or DisabledAiRankingScorer()
        self.score_client = score_client or DisabledRankingScoreClient()
        self._monitor_state: dict[tuple[str, str | None], list[RankingItem]] = {}

    async def get_ranking(
        self,
        ranking_type: str,
        exchange: str | None = None,
        limit: int = 50,
    ) -> list[RankingItem]:
        normalized_type = self._normalize_type(ranking_type)
        feature_values = await self.feature_repository.list_features()
        by_symbol: dict[tuple[str, str], dict[str, float]] = {}
        timestamps: dict[tuple[str, str], int] = {}

        for value in feature_values:
            if exchange and value.exchange.lower() != exchange.lower():
                continue
            key = (value.exchange.lower(), value.symbol.upper())
            by_symbol.setdefault(key, {})[value.feature] = value.value
            timestamps[key] = max(timestamps.get(key, 0), value.timestamp)

        items: list[RankingItem] = []
        for (item_exchange, symbol), factors in by_symbol.items():
            items.append(
                await self._build_ranking_item(
                    ranking_type=normalized_type,
                    symbol=symbol,
                    exchange=item_exchange,
                    timestamp=timestamps[(item_exchange, symbol)],
                    factors=factors,
                )
            )
        items = [item for item in items if item.score > 0]
        items.sort(key=lambda item: item.score, reverse=True)

        ranked = [
            model_copy_with_update(item, {"rank": index})
            for index, item in enumerate(items[: max(1, min(limit, 100))], start=1)
        ]
        if not ranked:
            raise ServiceError(4003, "No data")
        return ranked

    async def monitor_ranking(
        self,
        ranking_type: str,
        exchange: str | None = None,
        limit: int = 50,
        min_score: float | None = None,
        max_score: float | None = None,
    ) -> RankingMonitorSnapshot:
        normalized_type = self._normalize_type(ranking_type)
        threshold = (
            min_score
            if min_score is not None
            else MONITOR_DEFAULT_THRESHOLDS.get(normalized_type, 70.0)
        )
        upper_bound = (
            max_score
            if max_score is not None
            else MONITOR_DEFAULT_MAX_SCORES.get(normalized_type)
        )
        ranking = await self.get_ranking(normalized_type, exchange=exchange, limit=limit)
        eligible = [item for item in ranking if item.score >= threshold]
        if upper_bound is not None:
            eligible = [item for item in eligible if item.score <= upper_bound]
        active = [
            model_copy_with_update(item, {"rank": index})
            for index, item in enumerate(eligible, start=1)
        ]
        key = (normalized_type, exchange.lower() if exchange else None)
        previous = self._monitor_state.get(key, [])
        changes = self._diff_monitor(previous, active)
        changes = model_copy_with_update(
            changes,
            {
                "strategyEvents": self._strategy_events(
                    normalized_type,
                    previous,
                    active,
                    changes,
                )
            },
        )
        self._monitor_state[key] = active
        return RankingMonitorSnapshot(
            rankingType=normalized_type,
            exchange=exchange.lower() if exchange else None,
            updatedAt=now_ms(),
            active=active,
            changes=changes,
            summary=self._monitor_summary(normalized_type, active, changes, threshold, upper_bound),
        )

    async def _build_ranking_item(
        self,
        ranking_type: str,
        symbol: str,
        exchange: str,
        timestamp: int,
        factors: dict[str, float],
    ) -> RankingItem:
        score_result = await self.score_client.score(ranking_type, symbol, exchange, factors)
        if score_result:
            item = RankingItem(
                rank=0,
                symbol=symbol,
                exchange=exchange,
                score=round(score_result.score, 4),
                confidence=round(score_result.confidence, 4),
                timestamp=timestamp,
                factors=score_result.factors,
                modelVersion=score_result.modelVersion,
                opportunityScore=score_result.opportunityScore,
                riskScore=score_result.riskScore,
                riskWarning=score_result.riskWarning,
            )
            return self._attach_strategy_view(item, ranking_type, factors)

        ai_score = None
        if ranking_type in {"overall", "longInflow"}:
            ai_score = await self.ai_scorer.score(symbol, exchange, factors)

        if ai_score:
            item = RankingItem(
                rank=0,
                symbol=symbol,
                exchange=exchange,
                score=round(ai_score.overallScore, 4),
                confidence=round(ai_score.confidence, 4),
                timestamp=timestamp,
                factors={**factors, **ai_score.factors},
                modelVersion=ai_score.modelVersion,
                opportunityScore=ai_score.opportunityScore,
                riskScore=ai_score.riskScore,
                riskWarning=ai_score.riskWarning,
            )
            return self._attach_strategy_view(item, ranking_type, factors)

        item = RankingItem(
            rank=0,
            symbol=symbol,
            exchange=exchange,
            score=self._score(ranking_type, factors),
            confidence=self._confidence(factors),
            timestamp=timestamp,
            factors=factors,
        )
        return self._attach_strategy_view(item, ranking_type, factors)

    def _normalize_type(self, ranking_type: str) -> str:
        if ranking_type == "overall":
            return ranking_type
        if ranking_type not in RANKING_FEATURES:
            raise ServiceError(4002, "Invalid ranking type")
        return ranking_type

    def _score(self, ranking_type: str, factors: dict[str, float]) -> float:
        if ranking_type == "overall":
            long_score = factors.get("long_inflow_score", 0.0)
            momentum = max(0.0, factors.get("price_momentum", 0.0)) * 10.0
            volume = factors.get("volume_activity", 0.0)
            return round(min(100.0, long_score * 0.5 + momentum * 0.3 + volume * 0.2), 4)

        if ranking_type == "abnormalBullish":
            momentum = max(0.0, factors.get("price_momentum", 0.0)) * 10.0
            volume = factors.get("volume_activity", 0.0)
            long_score = factors.get("long_inflow_score", 0.0)
            derivative_pressure = self._derivative_pressure(factors)
            raw_score = momentum * 0.45 + volume * 0.25 + long_score * 0.30
            return round(min(100.0, raw_score + max(0.0, derivative_pressure - 45.0) * 0.10), 4)

        if ranking_type == "opportunityBullish":
            long_score = factors.get("long_inflow_score", 0.0)
            momentum = max(0.0, factors.get("price_momentum", 0.0)) * 10.0
            volume = factors.get("volume_activity", 0.0)
            derivative_pressure = self._derivative_pressure(factors)
            derivative_support = self._derivative_support(factors)
            raw_score = (
                long_score * 0.45
                + momentum * 0.25
                + volume * 0.20
                + derivative_support * 0.10
                - derivative_pressure * 0.15
            )
            return round(min(100.0, max(0.0, raw_score)), 4)

        if ranking_type == "riskBearish":
            negative_momentum = max(0.0, -factors.get("price_momentum", 0.0)) * 10.0
            weak_inflow = max(0.0, 100.0 - factors.get("long_inflow_score", 0.0))
            volume = factors.get("volume_activity", 0.0)
            derivative_pressure = self._derivative_pressure(factors)
            return round(
                min(
                    100.0,
                    negative_momentum * 0.45
                    + weak_inflow * 0.20
                    + volume * 0.15
                    + derivative_pressure * 0.20,
                ),
                4,
            )

        feature_name = RANKING_FEATURES[ranking_type]
        value = factors.get(feature_name, 0.0)
        if feature_name == "price_momentum":
            value = max(0.0, value) * 10.0
        return round(min(100.0, value), 4)

    @staticmethod
    def _confidence(factors: dict[str, float]) -> float:
        required = {
            "price_momentum",
            "volume_activity",
            "long_inflow_score",
            "main_force_net_inflow",
            "support_level",
            "resistance_level",
        }
        coverage = len(required.intersection(factors)) / len(required)
        return round(coverage, 4)

    def _attach_strategy_view(
        self,
        item: RankingItem,
        ranking_type: str,
        factors: dict[str, float],
    ) -> RankingItem:
        strategy = self._strategy_view(ranking_type, item.symbol, item.score, factors)
        return model_copy_with_update(item, strategy)

    def _strategy_view(
        self,
        ranking_type: str,
        symbol: str,
        score: float,
        factors: dict[str, float],
    ) -> dict[str, object]:
        momentum = factors.get("price_momentum", 0.0)
        volume = factors.get("volume_activity", 0.0)
        long_score = factors.get("long_inflow_score", 0.0)
        net_inflow = factors.get("main_force_net_inflow", 0.0)
        derivative_pressure = self._derivative_pressure(factors)
        derivative_support = self._derivative_support(factors)
        tags = self._reason_tags(momentum, volume, long_score, net_inflow, derivative_pressure)

        if ranking_type == "abnormalBullish":
            fomo = score >= 90 or derivative_pressure >= 55
            return {
                "strategyState": "fomo_watch" if fomo else "abnormal_breakout",
                "signalColor": "orange" if fomo else "green",
                "reasonTags": tags + (["fomo_risk"] if fomo else []),
                "guidance": (
                    "Abnormal bullish activity is strong but FOMO risk is elevated; avoid chasing "
                    "without support confirmation."
                    if fomo
                    else (
                        "Abnormal bullish activity is active; track first entries and confirm with "
                        "main-force support."
                    )
                ),
            }

        if ranking_type == "opportunityBullish":
            if 55 <= score <= 80 and derivative_pressure < 35:
                state = "steady_trend_candidate"
                color = "green"
                guidance = (
                    "Score is in the 55-80 opportunity band; suitable for trend watch while BTC "
                    "market status remains supportive."
                )
            elif score > 80 or derivative_pressure >= 35:
                state = "overheated_opportunity"
                color = "orange"
                guidance = (
                    "Opportunity score is overheated or derivatives pressure is rising; reduce "
                    "position aggressiveness."
                )
            else:
                state = "weak_opportunity"
                color = "gray"
                guidance = (
                    "Opportunity conditions are incomplete; wait for stronger trend confirmation."
                )
            return {
                "strategyState": state,
                "signalColor": color,
                "reasonTags": tags + (["derivative_support"] if derivative_support >= 35 else []),
                "guidance": guidance,
            }

        if ranking_type == "riskBearish":
            severe = score >= 80 or derivative_pressure >= 60
            return {
                "strategyState": "high_dump_risk" if severe else "bearish_risk_watch",
                "signalColor": "red" if severe else "orange",
                "reasonTags": tags,
                "guidance": (
                    "Bearish risk is high; reduce exposure and watch support breaks."
                    if severe
                    else "Bearish risk is present; review held positions and avoid weak rebounds."
                ),
            }

        return {
            "strategyState": ranking_type,
            "signalColor": "green" if score >= 70 else "gray",
            "reasonTags": tags,
            "guidance": None,
        }

    @staticmethod
    def _reason_tags(
        momentum: float,
        volume: float,
        long_score: float,
        net_inflow: float,
        derivative_pressure: float,
    ) -> list[str]:
        tags = []
        if momentum >= 5:
            tags.append("strong_momentum")
        elif momentum <= -5:
            tags.append("downside_pressure")
        if volume >= 70:
            tags.append("active_trading")
        if long_score >= 70:
            tags.append("main_force_inflow")
        if net_inflow < 0:
            tags.append("main_force_outflow")
        if derivative_pressure >= 35:
            tags.append("derivatives_pressure")
        return tags

    @staticmethod
    def _derivative_pressure(factors: dict[str, float]) -> float:
        pressure = 0.0
        pressure += max(0.0, factors.get("funding_pressure", 0.0)) * 0.20
        pressure += max(0.0, factors.get("open_interest_change", 0.0)) * 0.15
        pressure += max(0.0, factors.get("liquidation_pressure", 0.0)) * 0.35
        pressure += max(0.0, -factors.get("taker_buy_sell_imbalance", 0.0)) * 0.30
        return min(100.0, pressure)

    @staticmethod
    def _derivative_support(factors: dict[str, float]) -> float:
        support = 0.0
        support += max(0.0, -factors.get("funding_pressure", 0.0)) * 0.15
        support += max(0.0, -factors.get("liquidation_pressure", 0.0)) * 0.35
        support += max(0.0, factors.get("taker_buy_sell_imbalance", 0.0)) * 0.35
        support += max(0.0, factors.get("open_interest_change", 0.0)) * 0.15
        return min(100.0, support)

    @staticmethod
    def _identity(item: RankingItem) -> tuple[str, str]:
        return (item.exchange.lower(), item.symbol.upper())

    def _diff_monitor(
        self,
        previous: list[RankingItem],
        current: list[RankingItem],
    ) -> RankingMonitorChanges:
        previous_by_key = {
            self._identity(item): item
            for item in previous
        }
        current_by_key = {
            self._identity(item): item
            for item in current
        }

        entered = [
            RankingEntered(
                symbol=item.symbol,
                exchange=item.exchange,
                toRank=item.rank,
                score=item.score,
                item=item,
            )
            for key, item in current_by_key.items()
            if key not in previous_by_key
        ]
        exited = [
            RankingExited(
                symbol=item.symbol,
                exchange=item.exchange,
                fromRank=item.rank,
                previousScore=item.score,
                item=item,
            )
            for key, item in previous_by_key.items()
            if key not in current_by_key
        ]
        moved = []
        for key, item in current_by_key.items():
            previous_item = previous_by_key.get(key)
            if previous_item is None or previous_item.rank == item.rank:
                continue
            moved.append(
                RankingMoved(
                    symbol=item.symbol,
                    exchange=item.exchange,
                    fromRank=previous_item.rank,
                    toRank=item.rank,
                    previousScore=previous_item.score,
                    score=item.score,
                    scoreChange=round(item.score - previous_item.score, 4),
                    item=item,
                )
            )
        return RankingMonitorChanges(entered=entered, exited=exited, moved=moved)

    def _strategy_events(
        self,
        ranking_type: str,
        previous: list[RankingItem],
        active: list[RankingItem],
        changes: RankingMonitorChanges,
    ) -> list[RankingStrategyEvent]:
        events: list[RankingStrategyEvent] = []
        active_symbols = {item.symbol.upper() for item in active}
        previous_symbols = {item.symbol.upper() for item in previous}
        entered = list(changes.entered)
        exited = list(changes.exited)

        if ranking_type == "abnormalBullish":
            for change in entered:
                item = change.item
                event = (
                    "first_abnormal_fomo"
                    if item.strategyState == "fomo_watch"
                    else "first_abnormal"
                )
                title = f"{item.symbol} first abnormal bullish entry"
                body = (
                    "First abnormal bullish entry with FOMO pressure; confirm support "
                    "before chasing."
                    if event == "first_abnormal_fomo"
                    else "First abnormal bullish entry; track whether main-force inflow continues."
                )
                events.append(
                    RankingStrategyEvent(
                        event=event,
                        severity="warning" if event == "first_abnormal_fomo" else "info",
                        title=title,
                        body=body,
                        symbol=item.symbol,
                        item=item,
                        metadata={
                            "rankingType": ranking_type,
                            "score": item.score,
                            "strategyState": item.strategyState,
                        },
                    )
                )

        if ranking_type == "opportunityBullish":
            for symbol in ("BTCUSDT", "ETHUSDT"):
                if symbol in active_symbols and symbol not in previous_symbols:
                    events.append(
                        RankingStrategyEvent(
                            event=(
                                "market_trend_up"
                                if symbol == "BTCUSDT"
                                else "major_coin_entered"
                            ),
                            severity="info",
                            title=f"{symbol} entered opportunity bullish",
                            body=(
                                "BTC entered the opportunity monitor; market trend is treated "
                                "as bullish."
                                if symbol == "BTCUSDT"
                                else (
                                    "ETH entered the opportunity monitor; major-coin confirmation "
                                    "improved."
                                )
                            ),
                            symbol=symbol,
                            item=self._find_item(active, symbol),
                            metadata={"rankingType": ranking_type},
                        )
                    )
                if symbol not in active_symbols and symbol in previous_symbols:
                    events.append(
                        RankingStrategyEvent(
                            event=(
                                "market_trend_reversal_watch"
                                if symbol == "BTCUSDT"
                                else "major_coin_exited"
                            ),
                            severity="warning",
                            title=f"{symbol} exited opportunity bullish",
                            body=(
                                "BTC left the opportunity monitor; market may reverse into "
                                "downside or range."
                                if symbol == "BTCUSDT"
                                else (
                                    "ETH left the opportunity monitor; reduce aggressiveness on "
                                    "alt exposure."
                                )
                            ),
                            symbol=symbol,
                            item=self._find_item(previous, symbol),
                            metadata={"rankingType": ranking_type},
                        )
                    )

            if {"BTCUSDT", "ETHUSDT"}.issubset(previous_symbols) and not {
                "BTCUSDT",
                "ETHUSDT",
            }.intersection(active_symbols):
                events.append(
                    RankingStrategyEvent(
                        event="high_risk_sell_interpretation",
                        severity="critical",
                        title="BTC and ETH left opportunity bullish",
                        body="BTC and ETH both left the opportunity monitor; reduce exposure.",
                        metadata={"rankingType": ranking_type},
                    )
                )

        if ranking_type == "riskBearish":
            if len(entered) >= 5 or len(active) >= 10:
                events.append(
                        RankingStrategyEvent(
                            event="batch_risk_bearish",
                            severity="critical",
                            title="Batch risk bearish entries detected",
                            body=(
                                "Many symbols entered risk bearish together; market selloff "
                                "risk is elevated."
                            ),
                        metadata={
                            "rankingType": ranking_type,
                            "enteredCount": len(entered),
                            "activeCount": len(active),
                        },
                    )
                )
            for change in entered:
                if change.item.strategyState == "high_dump_risk":
                    events.append(
                        RankingStrategyEvent(
                            event="high_dump_risk",
                            severity="critical",
                            title=f"{change.symbol} high dump risk",
                            body=(
                                "High bearish risk detected; reduce exposure and watch support "
                                "breaks."
                            ),
                            symbol=change.symbol,
                            item=change.item,
                            metadata={"rankingType": ranking_type, "score": change.score},
                        )
                    )

        for change in exited:
            events.append(
                RankingStrategyEvent(
                    event="tracking_ended",
                    severity="info",
                    title=f"{change.symbol} tracking ended",
                    body="Symbol left the monitor; the tracked condition is no longer active.",
                    symbol=change.symbol,
                    item=change.item,
                    metadata={
                        "rankingType": ranking_type,
                        "previousScore": change.previousScore,
                    },
                )
            )
        return events

    @staticmethod
    def _find_item(items: list[RankingItem], symbol: str) -> RankingItem | None:
        normalized = symbol.upper()
        return next((item for item in items if item.symbol.upper() == normalized), None)

    def _monitor_summary(
        self,
        ranking_type: str,
        active: list[RankingItem],
        changes: RankingMonitorChanges,
        min_score: float,
        max_score: float | None,
    ) -> dict[str, object]:
        active_symbols = {item.symbol.upper() for item in active}
        entered_symbols = {item.symbol.upper() for item in changes.entered}
        exited_symbols = {item.symbol.upper() for item in changes.exited}
        summary: dict[str, object] = {
            "activeCount": len(active),
            "enteredCount": len(changes.entered),
            "exitedCount": len(changes.exited),
            "scoreBand": {
                "min": min_score,
                "max": max_score,
            },
        }

        if ranking_type == "opportunityBullish":
            btc_active = "BTCUSDT" in active_symbols
            btc_status = self._symbol_status(
                "BTCUSDT",
                active_symbols,
                entered_symbols,
                exited_symbols,
            )
            eth_status = self._symbol_status(
                "ETHUSDT",
                active_symbols,
                entered_symbols,
                exited_symbols,
            )
            guidance = (
                "BTC is in the opportunity monitor; treat the market as bullish trend."
                if btc_active
                else "BTC is not in the opportunity monitor; market may weaken or range."
            )
            risk_note = (
                "BTC and ETH both left the opportunity monitor; reduce exposure."
                if {"BTCUSDT", "ETHUSDT"}.issubset(exited_symbols)
                else None
            )
            summary.update(
                {
                    "btcStatus": btc_status,
                    "ethStatus": eth_status,
                    "marketBias": (
                        "uptrend"
                        if btc_active
                        else "down_or_sideways"
                    ),
                    "guidance": guidance,
                    "selectionRule": "Prefer opportunity candidates in the 55-80 score band.",
                    "riskNote": risk_note,
                }
            )

        if ranking_type == "riskBearish":
            batch_risk = len(changes.entered) >= 5 or len(active) >= 10
            summary.update(
                {
                    "batchRisk": batch_risk,
                    "marketBias": "selloff_risk" if batch_risk else "localized_risk",
                    "guidance": (
                        "Many symbols entered risk bearish together; reduce exposure."
                        if batch_risk
                        else "Risk bearish monitor is active; review held positions."
                    ),
                }
            )

        if ranking_type == "abnormalBullish":
            summary.update(
                {
                    "guidance": (
                        "First abnormal entries are high-attention candidates; "
                        "high-score surges may imply FOMO risk."
                    ),
                    "fomoSymbols": [
                        item.symbol
                        for item in active
                        if item.score >= 90
                    ],
                }
            )

        return summary

    @staticmethod
    def _symbol_status(
        symbol: str,
        active_symbols: set[str],
        entered_symbols: set[str],
        exited_symbols: set[str],
    ) -> str:
        if symbol in entered_symbols:
            return "entered"
        if symbol in exited_symbols:
            return "exited"
        if symbol in active_symbols:
            return "active"
        return "inactive"
