from typing import Protocol

from mip_common.events import MarketEvent, MarketTickerData
from mip_common.models import model_to_dict
from mip_common.responses import now_ms

from .binance import BinanceTickerConnector


class TickerConnector(Protocol):
    async def fetch_ticker(self, symbol: str) -> MarketEvent:
        ...

    async def fetch_funding(self, symbol: str) -> MarketEvent:
        ...

    async def fetch_open_interest(self, symbol: str) -> MarketEvent:
        ...

    async def fetch_liquidations(self, symbol: str, limit: int = 20) -> list[MarketEvent]:
        ...


class MockTickerConnector:
    async def fetch_ticker(self, symbol: str) -> MarketEvent:
        ticker = MarketTickerData(
            symbol=symbol.upper(),
            price=68000.0 if symbol.upper() == "BTCUSDT" else 3500.0,
            change24h=0.0,
            volume24h=1000000.0,
            source="mock",
        )
        return MarketEvent(
            event="market.ticker",
            exchange="mock",
            timestamp=now_ms(),
            data=model_to_dict(ticker),
        )

    async def fetch_funding(self, symbol: str) -> MarketEvent:
        return MarketEvent(
            event="market.funding",
            exchange="mock",
            timestamp=now_ms(),
            data={
                "symbol": symbol.upper(),
                "exchange": "mock",
                "fundingRate": 0.0001,
                "nextFundingTime": now_ms() + 8 * 60 * 60 * 1000,
                "source": "mock",
            },
        )

    async def fetch_open_interest(self, symbol: str) -> MarketEvent:
        return MarketEvent(
            event="market.open_interest",
            exchange="mock",
            timestamp=now_ms(),
            data={
                "symbol": symbol.upper(),
                "exchange": "mock",
                "openInterest": 1_000_000_000,
                "changeRate": 2.5,
                "source": "mock",
            },
        )

    async def fetch_liquidations(self, symbol: str, limit: int = 20) -> list[MarketEvent]:
        return [
            MarketEvent(
                event="market.liquidation",
                exchange="mock",
                timestamp=now_ms(),
                data={
                    "symbol": symbol.upper(),
                    "exchange": "mock",
                    "side": "long",
                    "price": 67000,
                    "quantity": 1.5,
                    "value": 100500,
                    "source": "mock",
                },
            )
        ][:limit]


def create_ticker_connector(exchange: str) -> TickerConnector:
    normalized = exchange.lower()
    if normalized == "binance":
        return BinanceTickerConnector()
    if normalized == "mock":
        return MockTickerConnector()
    raise ValueError(f"Unsupported collector exchange: {exchange}")
