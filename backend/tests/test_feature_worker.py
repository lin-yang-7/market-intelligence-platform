import pytest
from services.feature_service.app import worker
from services.feature_service.app.repositories import InMemoryFeatureRepository
from services.feature_service.app.services import FeatureService


@pytest.mark.asyncio
async def test_feature_worker_calculates_and_publishes_derivative_features(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = FeatureService(InMemoryFeatureRepository())
    published = []

    async def fake_publish(features):
        published.extend(features)

    monkeypatch.setattr(worker, "get_feature_service", lambda: service)
    monkeypatch.setattr(worker, "publish_feature_updates", fake_publish)

    funding = await worker.handle_event(
        {
            "event": "market.funding",
            "exchange": "binance",
            "timestamp": 1700000000000,
            "data": {"symbol": "BTCUSDT", "fundingRate": 0.0008},
        }
    )
    open_interest = await worker.handle_event(
        {
            "event": "market.open_interest",
            "exchange": "binance",
            "timestamp": 1700000001000,
            "data": {"symbol": "BTCUSDT", "openInterest": 1_000_000, "changeRate": 12.5},
        }
    )
    liquidation = await worker.handle_event(
        {
            "event": "market.liquidation",
            "exchange": "binance",
            "timestamp": 1700000002000,
            "data": {"symbol": "BTCUSDT", "side": "long", "value": 250_000},
        }
    )
    trade = await worker.handle_event(
        {
            "event": "market.trade",
            "exchange": "binance",
            "timestamp": 1700000003000,
            "data": {"symbol": "BTCUSDT", "side": "sell", "price": 68000, "quantity": 2},
        }
    )

    names = {item.feature for item in [*funding, *open_interest, *liquidation, *trade]}

    assert names == {
        "funding_pressure",
        "open_interest_change",
        "liquidation_pressure",
        "taker_buy_sell_imbalance",
    }
    assert {item.feature for item in published} == names
    assert (await service.get_current_feature("BTCUSDT", "funding_pressure", "binance")).value == 80
    assert (
        await service.get_current_feature("BTCUSDT", "taker_buy_sell_imbalance", "binance")
    ).value == -100

