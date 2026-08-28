import json
from typing import Protocol

from mip_common.events import MarketEvent
from mip_common.models import model_to_json, validate_model
from mip_common.redis import redis_get_json_list, redis_set_json_list

from .schemas import (
    FundingRateResponse,
    KlineResponse,
    LiquidationResponse,
    OpenInterestResponse,
    TickerResponse,
    TradeResponse,
)


class TickerRepository(Protocol):
    async def get_ticker(self, symbol: str, exchange: str | None = None) -> TickerResponse | None:
        ...

    async def save_ticker(self, event: MarketEvent) -> None:
        ...


class MarketRepository(TickerRepository, Protocol):
    async def list_klines(
        self,
        symbol: str,
        interval: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[KlineResponse]:
        ...

    async def list_trades(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[TradeResponse]:
        ...

    async def list_funding_rates(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[FundingRateResponse]:
        ...

    async def list_open_interest(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[OpenInterestResponse]:
        ...

    async def list_liquidations(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[LiquidationResponse]:
        ...

    async def save_klines(self, klines: list[KlineResponse]) -> None:
        ...

    async def save_trades(self, trades: list[TradeResponse]) -> None:
        ...

    async def save_funding_rates(self, funding_rates: list[FundingRateResponse]) -> None:
        ...

    async def save_open_interest(self, open_interest: list[OpenInterestResponse]) -> None:
        ...

    async def save_liquidations(self, liquidations: list[LiquidationResponse]) -> None:
        ...


class InMemoryTickerRepository:
    def __init__(self) -> None:
        self._tickers: dict[tuple[str, str], TickerResponse] = {}
        self._klines: list[KlineResponse] = []
        self._trades: list[TradeResponse] = []
        self._funding_rates: list[FundingRateResponse] = []
        self._open_interest: list[OpenInterestResponse] = []
        self._liquidations: list[LiquidationResponse] = []

    async def get_ticker(self, symbol: str, exchange: str | None = None) -> TickerResponse | None:
        symbol = symbol.upper()
        if exchange:
            return self._tickers.get((exchange.lower(), symbol))
        candidates = [
            ticker
            for (_ticker_exchange, ticker_symbol), ticker in self._tickers.items()
            if ticker_symbol == symbol
        ]
        return candidates[0] if candidates else None

    async def save_ticker(self, event: MarketEvent) -> None:
        ticker = TickerResponse(
            symbol=str(event.data["symbol"]).upper(),
            exchange=event.exchange.lower(),
            price=float(event.data["price"]),
            change24h=event.data.get("change24h"),
            volume24h=event.data.get("volume24h"),
            timestamp=event.timestamp,
            source=str(event.data.get("source", "exchange")),
        )
        self._tickers[(ticker.exchange, ticker.symbol)] = ticker

    async def list_klines(
        self,
        symbol: str,
        interval: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[KlineResponse]:
        symbol = symbol.upper()
        interval = interval.lower()
        klines = [
            kline
            for kline in self._klines
            if kline.symbol == symbol
            and kline.interval == interval
            and (exchange is None or kline.exchange == exchange.lower())
            and (start_time is None or kline.timestamp >= start_time)
            and (end_time is None or kline.timestamp <= end_time)
        ]
        klines.sort(key=lambda item: item.timestamp)
        return klines[-limit:]

    async def list_trades(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[TradeResponse]:
        symbol = symbol.upper()
        trades = [
            trade
            for trade in self._trades
            if trade.symbol == symbol
            and (exchange is None or trade.exchange == exchange.lower())
            and (start_time is None or trade.timestamp >= start_time)
            and (end_time is None or trade.timestamp <= end_time)
        ]
        trades.sort(key=lambda item: item.timestamp, reverse=True)
        return trades[:limit]

    async def save_klines(self, klines: list[KlineResponse]) -> None:
        self._klines.extend(klines)

    async def save_trades(self, trades: list[TradeResponse]) -> None:
        self._trades.extend(trades)

    async def list_funding_rates(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[FundingRateResponse]:
        values = self._filter_symbol_time(
            self._funding_rates,
            symbol,
            exchange,
            start_time,
            end_time,
        )
        values.sort(key=lambda item: item.timestamp, reverse=True)
        return values[:limit]

    async def list_open_interest(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[OpenInterestResponse]:
        values = self._filter_symbol_time(
            self._open_interest,
            symbol,
            exchange,
            start_time,
            end_time,
        )
        values.sort(key=lambda item: item.timestamp, reverse=True)
        return values[:limit]

    async def list_liquidations(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[LiquidationResponse]:
        values = self._filter_symbol_time(
            self._liquidations,
            symbol,
            exchange,
            start_time,
            end_time,
        )
        values.sort(key=lambda item: item.timestamp, reverse=True)
        return values[:limit]

    async def save_funding_rates(self, funding_rates: list[FundingRateResponse]) -> None:
        self._funding_rates.extend(funding_rates)

    async def save_open_interest(self, open_interest: list[OpenInterestResponse]) -> None:
        self._open_interest.extend(open_interest)

    async def save_liquidations(self, liquidations: list[LiquidationResponse]) -> None:
        self._liquidations.extend(liquidations)

    @staticmethod
    def _filter_symbol_time(
        values,
        symbol: str,
        exchange: str | None,
        start_time: int | None,
        end_time: int | None,
    ):
        symbol = symbol.upper()
        return [
            value
            for value in values
            if value.symbol == symbol
            and (exchange is None or value.exchange == exchange.lower())
            and (start_time is None or value.timestamp >= start_time)
            and (end_time is None or value.timestamp <= end_time)
        ]


class RedisTickerRepository:
    def __init__(self, redis_client) -> None:
        self.redis = redis_client

    async def get_ticker(self, symbol: str, exchange: str | None = None) -> TickerResponse | None:
        symbol = symbol.upper()
        if exchange:
            payload = await self.redis.get(self._exchange_key(symbol, exchange))
            return self._decode(payload) if payload else None

        payload = await self.redis.get(self._symbol_key(symbol))
        return self._decode(payload) if payload else None

    async def save_ticker(self, event: MarketEvent) -> None:
        ticker = TickerResponse(
            symbol=str(event.data["symbol"]).upper(),
            exchange=event.exchange.lower(),
            price=float(event.data["price"]),
            change24h=event.data.get("change24h"),
            volume24h=event.data.get("volume24h"),
            timestamp=event.timestamp,
            source=str(event.data.get("source", "exchange")),
        )
        payload = model_to_json(ticker)
        await self.redis.set(self._symbol_key(ticker.symbol), payload, ex=10)
        await self.redis.set(self._exchange_key(ticker.symbol, ticker.exchange), payload, ex=10)

    async def list_klines(
        self,
        symbol: str,
        interval: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[KlineResponse]:
        values = await self._load_klines(symbol, interval, exchange or "default")
        values = [
            value
            for value in values
            if (exchange is None or value.exchange == exchange.lower())
            and (start_time is None or value.timestamp >= start_time)
            and (end_time is None or value.timestamp <= end_time)
        ]
        values.sort(key=lambda value: value.timestamp)
        return values[-limit:]

    async def list_trades(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[TradeResponse]:
        values = await self._load_trades(symbol, exchange or "default")
        values = [
            value
            for value in values
            if (exchange is None or value.exchange == exchange.lower())
            and (start_time is None or value.timestamp >= start_time)
            and (end_time is None or value.timestamp <= end_time)
        ]
        values.sort(key=lambda value: value.timestamp, reverse=True)
        return values[:limit]

    async def save_klines(self, klines: list[KlineResponse]) -> None:
        grouped: dict[tuple[str, str, str], list[KlineResponse]] = {}
        for kline in klines:
            key = (kline.exchange.lower(), kline.symbol.upper(), kline.interval.lower())
            grouped.setdefault(key, []).append(kline)
        for (exchange, symbol, interval), items in grouped.items():
            existing = await self._load_klines(symbol, interval, exchange)
            existing.extend(items)
            existing.sort(key=lambda value: value.timestamp)
            await redis_set_json_list(
                self.redis,
                self._kline_key(exchange, symbol, interval),
                existing,
            )

    async def save_trades(self, trades: list[TradeResponse]) -> None:
        grouped: dict[tuple[str, str], list[TradeResponse]] = {}
        for trade in trades:
            key = (trade.exchange.lower(), trade.symbol.upper())
            grouped.setdefault(key, []).append(trade)
        for (exchange, symbol), items in grouped.items():
            existing = await self._load_trades(symbol, exchange)
            existing.extend(items)
            existing.sort(key=lambda value: value.timestamp, reverse=True)
            await redis_set_json_list(self.redis, self._trade_key(exchange, symbol), existing)

    async def list_funding_rates(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[FundingRateResponse]:
        values = await self._load_list(
            self._funding_key(exchange or "default", symbol),
            FundingRateResponse,
        )
        return self._filter_and_limit(values, exchange, start_time, end_time, limit)

    async def list_open_interest(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[OpenInterestResponse]:
        values = await self._load_list(
            self._open_interest_key(exchange or "default", symbol),
            OpenInterestResponse,
        )
        return self._filter_and_limit(values, exchange, start_time, end_time, limit)

    async def list_liquidations(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[LiquidationResponse]:
        values = await self._load_list(
            self._liquidation_key(exchange or "default", symbol),
            LiquidationResponse,
        )
        return self._filter_and_limit(values, exchange, start_time, end_time, limit)

    async def save_funding_rates(self, funding_rates: list[FundingRateResponse]) -> None:
        await self._save_grouped(funding_rates, self._funding_key, FundingRateResponse)

    async def save_open_interest(self, open_interest: list[OpenInterestResponse]) -> None:
        await self._save_grouped(open_interest, self._open_interest_key, OpenInterestResponse)

    async def save_liquidations(self, liquidations: list[LiquidationResponse]) -> None:
        await self._save_grouped(liquidations, self._liquidation_key, LiquidationResponse)

    @staticmethod
    def _symbol_key(symbol: str) -> str:
        return f"market:ticker:{symbol.upper()}"

    @staticmethod
    def _exchange_key(symbol: str, exchange: str) -> str:
        return f"market:ticker:{exchange.lower()}:{symbol.upper()}"

    @staticmethod
    def _decode(payload: bytes | str) -> TickerResponse:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return validate_model(TickerResponse, json.loads(payload))

    async def _load_klines(
        self,
        symbol: str,
        interval: str,
        exchange: str,
    ) -> list[KlineResponse]:
        rows = await redis_get_json_list(self.redis, self._kline_key(exchange, symbol, interval))
        return [validate_model(KlineResponse, row) for row in rows]

    async def _load_trades(self, symbol: str, exchange: str) -> list[TradeResponse]:
        rows = await redis_get_json_list(self.redis, self._trade_key(exchange, symbol))
        return [validate_model(TradeResponse, row) for row in rows]

    async def _load_list(self, key: str, model):
        rows = await redis_get_json_list(self.redis, key)
        return [validate_model(model, row) for row in rows]

    def _filter_and_limit(
        self,
        values,
        exchange: str | None,
        start_time: int | None,
        end_time: int | None,
        limit: int,
    ):
        values = [
            value
            for value in values
            if (exchange is None or value.exchange == exchange.lower())
            and (start_time is None or value.timestamp >= start_time)
            and (end_time is None or value.timestamp <= end_time)
        ]
        values.sort(key=lambda value: value.timestamp, reverse=True)
        return values[:limit]

    async def _save_grouped(self, items, key_factory, model) -> None:
        grouped: dict[tuple[str, str], list] = {}
        for item in items:
            key = (item.exchange.lower(), item.symbol.upper())
            grouped.setdefault(key, []).append(item)
        for (exchange, symbol), rows in grouped.items():
            key = key_factory(exchange, symbol)
            existing = [
                validate_model(model, row)
                for row in await redis_get_json_list(self.redis, key)
            ]
            existing.extend(rows)
            existing.sort(key=lambda value: value.timestamp, reverse=True)
            await redis_set_json_list(self.redis, key, existing)

    @staticmethod
    def _kline_key(exchange: str, symbol: str, interval: str) -> str:
        return f"market:kline:{exchange.lower()}:{symbol.upper()}:{interval.lower()}"

    @staticmethod
    def _trade_key(exchange: str, symbol: str) -> str:
        return f"market:trade:{exchange.lower()}:{symbol.upper()}"

    @staticmethod
    def _funding_key(exchange: str, symbol: str) -> str:
        return f"market:funding:{exchange.lower()}:{symbol.upper()}"

    @staticmethod
    def _open_interest_key(exchange: str, symbol: str) -> str:
        return f"market:open_interest:{exchange.lower()}:{symbol.upper()}"

    @staticmethod
    def _liquidation_key(exchange: str, symbol: str) -> str:
        return f"market:liquidation:{exchange.lower()}:{symbol.upper()}"
