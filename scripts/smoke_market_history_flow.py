import asyncio

from mip_common.models import model_to_dict
from services.market_service.app.repositories import InMemoryTickerRepository
from services.market_service.app.schemas import KlineResponse, TradeResponse
from services.market_service.app.services import MarketService


async def main() -> None:
    service = MarketService(InMemoryTickerRepository())
    await service.save_klines(
        [
            KlineResponse(
                symbol="BTCUSDT",
                exchange="binance",
                interval="1m",
                timestamp=1700000000000,
                open=67000,
                high=68000,
                low=66500,
                close=67500,
                volume=10000,
                quoteVolume=675000000,
                source="smoke",
            ),
            KlineResponse(
                symbol="BTCUSDT",
                exchange="binance",
                interval="1m",
                timestamp=1700000060000,
                open=67500,
                high=68200,
                low=67400,
                close=68100,
                volume=12000,
                quoteVolume=817200000,
                source="smoke",
            ),
        ]
    )
    await service.save_trades(
        [
            TradeResponse(
                symbol="BTCUSDT",
                exchange="binance",
                tradeId="t1",
                price=68000,
                quantity=1.2,
                side="buy",
                timestamp=1700000061000,
                source="smoke",
            ),
            TradeResponse(
                symbol="BTCUSDT",
                exchange="binance",
                tradeId="t2",
                price=67900,
                quantity=0.8,
                side="sell",
                timestamp=1700000062000,
                source="smoke",
            ),
        ]
    )

    klines = await service.get_klines("BTCUSDT", "1m", exchange="binance")
    trades = await service.get_trades("BTCUSDT", exchange="binance")
    print([model_to_dict(kline) for kline in klines])
    print([model_to_dict(trade) for trade in trades])


if __name__ == "__main__":
    asyncio.run(main())
