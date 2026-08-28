import hashlib

from mip_common.responses import ServiceError
from services.ranking_service.app.schemas import RankingItem

from .repositories import SignalRepository
from .schemas import Signal

SUPPORTED_SIGNAL_TYPES = {"longInflow", "momentum", "breakout", "volatility", "reversal"}


class SignalService:
    def __init__(self, repository: SignalRepository) -> None:
        self.repository = repository

    async def generate_from_ranking(
        self,
        ranking_type: str,
        ranking: list[RankingItem],
        min_score: float = 70.0,
    ) -> list[Signal]:
        signal_type = self._signal_type_from_ranking(ranking_type)
        signals = [
            self._create_signal(signal_type, item)
            for item in ranking
            if item.score >= min_score
        ]
        await self.repository.save_signals(signals)
        return signals

    async def current(
        self,
        symbol: str | None = None,
        signal_type: str | None = None,
        limit: int = 50,
    ) -> list[Signal]:
        self._validate_signal_type(signal_type)
        signals = await self.repository.list_current(symbol, signal_type, limit)
        if not signals:
            raise ServiceError(6001, "Signal unavailable")
        return signals

    async def long_inflow(self, limit: int = 50) -> list[Signal]:
        return await self.current(signal_type="longInflow", limit=limit)

    async def detail(self, signal_id: str) -> Signal:
        signal = await self.repository.get_signal(signal_id)
        if signal is None:
            raise ServiceError(6003, "Signal not found")
        return signal

    async def history(
        self,
        symbol: str,
        signal_type: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[Signal]:
        self._validate_signal_type(signal_type)
        self._validate_time_range(start_time, end_time)
        signals = await self.repository.list_history(
            symbol=symbol,
            signal_type=signal_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        if not signals:
            raise ServiceError(6001, "Signal unavailable")
        return signals

    def _signal_type_from_ranking(self, ranking_type: str) -> str:
        if ranking_type == "longInflow":
            return "longInflow"
        if ranking_type == "momentum":
            return "momentum"
        if ranking_type == "volume":
            return "breakout"
        if ranking_type == "overall":
            return "momentum"
        raise ServiceError(6002, "Invalid signal type")

    def _validate_signal_type(self, signal_type: str | None) -> None:
        if signal_type and signal_type not in SUPPORTED_SIGNAL_TYPES:
            raise ServiceError(6002, "Invalid signal type")

    @staticmethod
    def _validate_time_range(start_time: int | None, end_time: int | None) -> None:
        if start_time is not None and start_time < 0:
            raise ServiceError(2003, "Invalid time range")
        if end_time is not None and end_time < 0:
            raise ServiceError(2003, "Invalid time range")
        if start_time is not None and end_time is not None and start_time > end_time:
            raise ServiceError(2003, "Invalid time range")

    def _create_signal(self, signal_type: str, item: RankingItem) -> Signal:
        reasons = self._reasons(signal_type, item.factors)
        signal_id = self._signal_id(signal_type, item.exchange, item.symbol, item.timestamp)
        return Signal(
            signalId=signal_id,
            symbol=item.symbol,
            exchange=item.exchange,
            type=signal_type,
            score=item.score,
            confidence=item.confidence,
            reasons=reasons,
            factors=item.factors,
            explanation=self._explanation(signal_type, reasons, item.riskWarning),
            timestamp=item.timestamp,
            modelVersion=item.modelVersion,
            opportunityScore=item.opportunityScore,
            riskScore=item.riskScore,
            riskWarning=item.riskWarning,
        )

    @staticmethod
    def _signal_id(signal_type: str, exchange: str, symbol: str, timestamp: int) -> str:
        raw = f"{signal_type}:{exchange}:{symbol}:{timestamp}".encode()
        digest = hashlib.sha1(raw).hexdigest()[:12]
        return f"sig_{digest}"

    @staticmethod
    def _reasons(signal_type: str, factors: dict[str, float]) -> list[str]:
        reasons: list[str] = []
        if signal_type == "longInflow" and factors.get("long_inflow_score", 0.0) >= 70:
            reasons.append("high_inflow")
        if factors.get("volume_activity", 0.0) >= 70:
            reasons.append("volume_breakout")
        if factors.get("price_momentum", 0.0) > 0:
            reasons.append("positive_momentum")
        return reasons or ["ranking_score_threshold"]

    @staticmethod
    def _explanation(
        signal_type: str,
        reasons: list[str],
        risk_warning: str | None = None,
    ) -> str:
        explanation = f"{signal_type} signal created: {', '.join(reasons)}"
        if risk_warning:
            return f"{explanation}. {risk_warning}"
        return explanation
