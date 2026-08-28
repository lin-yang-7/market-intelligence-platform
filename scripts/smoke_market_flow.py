import asyncio

from mip_common.events import MarketEvent
from mip_common.models import model_to_dict
from services.market_service.app.repositories import InMemoryTickerRepository
from services.market_service.app.services import MarketService


async def main() -> None:
    service = MarketService(InMemoryTickerRepository())
    await service.handle_market_ticker_event(
        MarketEvent(
            event="market.ticker",
            exchange="binance",
            timestamp=1700000000000,
            data={
                "symbol": "BTCUSDT",
                "price": 68000,
                "change24h": 2.5,
                "volume24h": 120000000,
                "source": "smoke",
            },
        )
    )
    ticker = await service.get_ticker("btcusdt", "binance")
    print(model_to_dict(ticker))


if __name__ == "__main__":
    asyncio.run(main())

