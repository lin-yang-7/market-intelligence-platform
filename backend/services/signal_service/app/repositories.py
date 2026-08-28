from typing import Protocol

from mip_common.models import validate_model
from mip_common.redis import (
    redis_get_json_list,
    redis_get_model,
    redis_set_json_list,
    redis_set_model,
)

from .schemas import Signal


class SignalRepository(Protocol):
    async def save_signals(self, signals: list[Signal]) -> None:
        ...

    async def list_current(
        self,
        symbol: str | None = None,
        signal_type: str | None = None,
        limit: int = 50,
    ) -> list[Signal]:
        ...

    async def get_signal(self, signal_id: str) -> Signal | None:
        ...

    async def list_history(
        self,
        symbol: str,
        signal_type: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[Signal]:
        ...


class InMemorySignalRepository:
    def __init__(self) -> None:
        self._signals: dict[str, Signal] = {}

    async def save_signals(self, signals: list[Signal]) -> None:
        for signal in signals:
            self._signals[signal.signalId] = signal

    async def list_current(
        self,
        symbol: str | None = None,
        signal_type: str | None = None,
        limit: int = 50,
    ) -> list[Signal]:
        signals = [signal for signal in self._signals.values() if signal.status == "active"]
        if symbol:
            signals = [signal for signal in signals if signal.symbol == symbol.upper()]
        if signal_type:
            signals = [signal for signal in signals if signal.type == signal_type]
        signals.sort(key=lambda signal: (signal.score, signal.timestamp), reverse=True)
        return signals[: max(1, min(limit, 100))]

    async def get_signal(self, signal_id: str) -> Signal | None:
        return self._signals.get(signal_id)

    async def list_history(
        self,
        symbol: str,
        signal_type: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[Signal]:
        signals = [signal for signal in self._signals.values() if signal.symbol == symbol.upper()]
        if signal_type:
            signals = [signal for signal in signals if signal.type == signal_type]
        if start_time is not None:
            signals = [signal for signal in signals if signal.timestamp >= start_time]
        if end_time is not None:
            signals = [signal for signal in signals if signal.timestamp <= end_time]
        signals.sort(key=lambda signal: signal.timestamp, reverse=True)
        return signals[: max(1, min(limit, 1000))]


class RedisSignalRepository:
    def __init__(self, redis_client, ttl_seconds: int = 300) -> None:
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds

    async def save_signals(self, signals: list[Signal]) -> None:
        existing = {signal.signalId: signal for signal in await self._all_signals()}
        for signal in signals:
            existing[signal.signalId] = signal
            await redis_set_model(
                self.redis,
                self._detail_key(signal.signalId),
                signal,
                self.ttl_seconds,
            )
        await redis_set_json_list(self.redis, self._index_key(), list(existing.values()))

    async def list_current(
        self,
        symbol: str | None = None,
        signal_type: str | None = None,
        limit: int = 50,
    ) -> list[Signal]:
        signals = [signal for signal in await self._all_signals() if signal.status == "active"]
        if symbol:
            signals = [signal for signal in signals if signal.symbol == symbol.upper()]
        if signal_type:
            signals = [signal for signal in signals if signal.type == signal_type]
        signals.sort(key=lambda signal: (signal.score, signal.timestamp), reverse=True)
        return signals[: max(1, min(limit, 100))]

    async def get_signal(self, signal_id: str) -> Signal | None:
        return await redis_get_model(self.redis, self._detail_key(signal_id), Signal)

    async def list_history(
        self,
        symbol: str,
        signal_type: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[Signal]:
        signals = [
            signal
            for signal in await self._all_signals()
            if signal.symbol == symbol.upper()
        ]
        if signal_type:
            signals = [signal for signal in signals if signal.type == signal_type]
        if start_time is not None:
            signals = [signal for signal in signals if signal.timestamp >= start_time]
        if end_time is not None:
            signals = [signal for signal in signals if signal.timestamp <= end_time]
        signals.sort(key=lambda signal: signal.timestamp, reverse=True)
        return signals[: max(1, min(limit, 1000))]

    async def _all_signals(self) -> list[Signal]:
        rows = await redis_get_json_list(self.redis, self._index_key())
        return [validate_model(Signal, row) for row in rows]

    @staticmethod
    def _detail_key(signal_id: str) -> str:
        return f"signal:{signal_id}"

    @staticmethod
    def _index_key() -> str:
        return "signal:latest"
