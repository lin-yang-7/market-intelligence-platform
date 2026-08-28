import pytest
from mip_common.kafka import serialize_event
from services.market_service.app import worker
from services.market_service.app.repositories import InMemoryTickerRepository
from services.market_service.app.services import MarketService


@pytest.mark.asyncio
async def test_market_worker_persists_derivative_events(monkeypatch: pytest.MonkeyPatch) -> None:
    service = MarketService(InMemoryTickerRepository())
    monkeypatch.setattr(worker, "get_market_service", lambda: service)

    await worker.handle_payload(
        serialize_event(
            {
                "event": "market.funding",
                "exchange": "binance",
                "timestamp": 1700000000000,
                "data": {
                    "symbol": "BTCUSDT",
                    "fundingRate": 0.0001,
                    "nextFundingTime": 1700007200000,
                },
            }
        )
    )
    await worker.handle_payload(
        serialize_event(
            {
                "event": "market.open_interest",
                "exchange": "binance",
                "timestamp": 1700000001000,
                "data": {
                    "symbol": "BTCUSDT",
                    "openInterest": 1_500_000,
                    "changeRate": 4.2,
                },
            }
        )
    )
    await worker.handle_payload(
        serialize_event(
            {
                "event": "market.liquidation",
                "exchange": "binance",
                "timestamp": 1700000002000,
                "data": {
                    "symbol": "BTCUSDT",
                    "side": "short",
                    "price": 67000,
                    "quantity": 3,
                },
            }
        )
    )

    funding = await service.get_funding_rates("BTCUSDT", "binance")
    open_interest = await service.get_open_interest("BTCUSDT", "binance")
    liquidations = await service.get_liquidations("BTCUSDT", "binance")

    assert funding[0].fundingRate == 0.0001
    assert open_interest[0].changeRate == 4.2
    assert liquidations[0].side == "short"
    assert liquidations[0].value == 201000

