import re

from mip_common.config import get_settings
from mip_common.events import MarketEvent
from mip_common.responses import ServiceError

from .repositories import MarketRepository
from .schemas import (
    FundingRateResponse,
    KlineResponse,
    LiquidationResponse,
    OpenInterestResponse,
    TickerResponse,
    TradeResponse,
)


class MarketService:
    symbol_pattern = re.compile(r"^[A-Z0-9]{3,30}$")
    interval_pattern = re.compile(r"^(1m|5m|15m|30m|1h|4h|1d)$")

    def __init__(self, repository: MarketRepository) -> None:
        self.repository = repository

    async def get_ticker(self, symbol: str, exchange: str | None = None) -> TickerResponse:
        normalized_symbol = symbol.upper()
        normalized_exchange = exchange.lower() if exchange else None
        self._validate_symbol(normalized_symbol)
        self._validate_exchange(normalized_exchange)
        ticker = await self.repository.get_ticker(normalized_symbol, normalized_exchange)
        if ticker is None:
            raise ServiceError(3001, "Symbol not found")
        return ticker

    async def handle_market_ticker_event(self, event: MarketEvent) -> None:
        if event.event != "market.ticker":
            raise ServiceError(2001, "Invalid event type")
        self._validate_exchange(event.exchange)
        symbol = str(event.data.get("symbol", "")).upper()
        self._validate_symbol(symbol)
        if "price" not in event.data or float(event.data["price"]) <= 0:
            raise ServiceError(2001, "Invalid price")
        await self.repository.save_ticker(event)

    async def handle_market_event(self, event: MarketEvent) -> None:
        if event.event == "market.ticker":
            await self.handle_market_ticker_event(event)
            return
        self._validate_exchange(event.exchange)
        symbol = str(event.data.get("symbol", "")).upper()
        self._validate_symbol(symbol)
        if event.event == "market.funding":
            await self.save_funding_rates(
                [
                    FundingRateResponse(
                        symbol=symbol,
                        exchange=event.exchange.lower(),
                        fundingRate=float(event.data.get("fundingRate") or 0.0),
                        nextFundingTime=int(event.data.get("nextFundingTime") or event.timestamp),
                        timestamp=event.timestamp,
                        source=str(event.data.get("source", "exchange")),
                    )
                ]
            )
            return
        if event.event == "market.open_interest":
            await self.save_open_interest(
                [
                    OpenInterestResponse(
                        symbol=symbol,
                        exchange=event.exchange.lower(),
                        openInterest=float(event.data.get("openInterest") or 0.0),
                        changeRate=float(event.data.get("changeRate") or 0.0),
                        timestamp=event.timestamp,
                        source=str(event.data.get("source", "exchange")),
                    )
                ]
            )
            return
        if event.event == "market.liquidation":
            price = float(event.data.get("price") or 0.0)
            quantity = float(event.data.get("quantity") or 0.0)
            await self.save_liquidations(
                [
                    LiquidationResponse(
                        symbol=symbol,
                        exchange=event.exchange.lower(),
                        side=str(event.data.get("side", "")),
                        price=price,
                        quantity=quantity,
                        value=float(event.data.get("value") or price * quantity),
                        timestamp=event.timestamp,
                        source=str(event.data.get("source", "exchange")),
                    )
                ]
            )
            return
        raise ServiceError(2001, "Invalid event type")

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[KlineResponse]:
        normalized_symbol = symbol.upper()
        normalized_interval = interval.lower()
        normalized_exchange = exchange.lower() if exchange else None
        self._validate_symbol(normalized_symbol)
        self._validate_interval(normalized_interval)
        self._validate_exchange(normalized_exchange)
        self._validate_time_range(start_time, end_time)
        klines = await self.repository.list_klines(
            normalized_symbol,
            normalized_interval,
            normalized_exchange,
            start_time,
            end_time,
            limit,
        )
        if not klines:
            raise ServiceError(3001, "Symbol not found")
        return klines

    async def get_trades(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[TradeResponse]:
        normalized_symbol = symbol.upper()
        normalized_exchange = exchange.lower() if exchange else None
        self._validate_symbol(normalized_symbol)
        self._validate_exchange(normalized_exchange)
        self._validate_time_range(start_time, end_time)
        trades = await self.repository.list_trades(
            normalized_symbol,
            normalized_exchange,
            start_time,
            end_time,
            limit,
        )
        if not trades:
            raise ServiceError(3001, "Symbol not found")
        return trades

    async def get_funding_rates(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[FundingRateResponse]:
        normalized_symbol = symbol.upper()
        normalized_exchange = exchange.lower() if exchange else None
        self._validate_symbol(normalized_symbol)
        self._validate_exchange(normalized_exchange)
        self._validate_time_range(start_time, end_time)
        values = await self.repository.list_funding_rates(
            normalized_symbol,
            normalized_exchange,
            start_time,
            end_time,
            limit,
        )
        if not values:
            raise ServiceError(3001, "Symbol not found")
        return values

    async def get_open_interest(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[OpenInterestResponse]:
        normalized_symbol = symbol.upper()
        normalized_exchange = exchange.lower() if exchange else None
        self._validate_symbol(normalized_symbol)
        self._validate_exchange(normalized_exchange)
        self._validate_time_range(start_time, end_time)
        values = await self.repository.list_open_interest(
            normalized_symbol,
            normalized_exchange,
            start_time,
            end_time,
            limit,
        )
        if not values:
            raise ServiceError(3001, "Symbol not found")
        return values

    async def get_liquidations(
        self,
        symbol: str,
        exchange: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[LiquidationResponse]:
        normalized_symbol = symbol.upper()
        normalized_exchange = exchange.lower() if exchange else None
        self._validate_symbol(normalized_symbol)
        self._validate_exchange(normalized_exchange)
        self._validate_time_range(start_time, end_time)
        values = await self.repository.list_liquidations(
            normalized_symbol,
            normalized_exchange,
            start_time,
            end_time,
            limit,
        )
        if not values:
            raise ServiceError(3001, "Symbol not found")
        return values

    async def save_klines(self, klines: list[KlineResponse]) -> None:
        for kline in klines:
            self._validate_symbol(kline.symbol)
            self._validate_exchange(kline.exchange)
            self._validate_interval(kline.interval)
            if min(kline.open, kline.high, kline.low, kline.close, kline.volume) < 0:
                raise ServiceError(2001, "Invalid market data")
        await self.repository.save_klines(klines)

    async def save_trades(self, trades: list[TradeResponse]) -> None:
        for trade in trades:
            self._validate_symbol(trade.symbol)
            self._validate_exchange(trade.exchange)
            if trade.side not in {"buy", "sell"}:
                raise ServiceError(2001, "Invalid side")
            if trade.price <= 0 or trade.quantity <= 0:
                raise ServiceError(2001, "Invalid market data")
        await self.repository.save_trades(trades)

    async def save_funding_rates(self, funding_rates: list[FundingRateResponse]) -> None:
        for funding in funding_rates:
            self._validate_symbol(funding.symbol)
            self._validate_exchange(funding.exchange)
            if abs(funding.fundingRate) > 1:
                raise ServiceError(2001, "Invalid funding rate")
        await self.repository.save_funding_rates(funding_rates)

    async def save_open_interest(self, open_interest: list[OpenInterestResponse]) -> None:
        for item in open_interest:
            self._validate_symbol(item.symbol)
            self._validate_exchange(item.exchange)
            if item.openInterest < 0:
                raise ServiceError(2001, "Invalid open interest")
        await self.repository.save_open_interest(open_interest)

    async def save_liquidations(self, liquidations: list[LiquidationResponse]) -> None:
        for item in liquidations:
            self._validate_symbol(item.symbol)
            self._validate_exchange(item.exchange)
            if item.side not in {"long", "short"}:
                raise ServiceError(2001, "Invalid side")
            if item.price <= 0 or item.quantity <= 0 or item.value <= 0:
                raise ServiceError(2001, "Invalid liquidation data")
        await self.repository.save_liquidations(liquidations)

    def _validate_symbol(self, symbol: str) -> None:
        if not self.symbol_pattern.match(symbol):
            raise ServiceError(2001, "Invalid symbol")

    def _validate_exchange(self, exchange: str | None) -> None:
        if exchange is None:
            return
        if exchange.lower() not in get_settings().supported_exchange_set:
            raise ServiceError(2002, "Invalid exchange")

    def _validate_interval(self, interval: str) -> None:
        if not self.interval_pattern.match(interval):
            raise ServiceError(2001, "Invalid interval")

    def _validate_time_range(self, start_time: int | None, end_time: int | None) -> None:
        if start_time is not None and start_time < 0:
            raise ServiceError(2003, "Invalid time range")
        if end_time is not None and end_time < 0:
            raise ServiceError(2003, "Invalid time range")
        if start_time is not None and end_time is not None and start_time > end_time:
            raise ServiceError(2003, "Invalid time range")
