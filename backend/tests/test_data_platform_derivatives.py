import pytest
from data_platform.app.processor import PipelineProcessor
from data_platform.app.schemas import PipelineEvent
from data_platform.app.storage import InMemoryEventStorage


@pytest.mark.asyncio
async def test_derivatives_events_are_routed_and_stored() -> None:
    processor = PipelineProcessor()
    storage = InMemoryEventStorage()
    events = [
        PipelineEvent(
            event_type="market.funding",
            timestamp=1700000000000,
            source="binance",
            data={
                "exchange": "binance",
                "symbol": "BTCUSDT",
                "fundingRate": 0.0001,
                "nextFundingTime": 1700007200000,
            },
        ),
        PipelineEvent(
            event_type="market.open_interest",
            timestamp=1700000001000,
            source="binance",
            data={
                "exchange": "binance",
                "symbol": "BTCUSDT",
                "openInterest": 1_000_000_000,
                "changeRate": 5.2,
            },
        ),
        PipelineEvent(
            event_type="market.liquidation",
            timestamp=1700000002000,
            source="binance",
            data={
                "exchange": "binance",
                "symbol": "BTCUSDT",
                "side": "long",
                "price": 67000,
                "quantity": 2,
                "value": 134000,
            },
        ),
    ]

    for event in events:
        result = await storage.write(processor.process(event))
        assert result.stored is True

    assert [row["symbol"] for row in storage.rows] == ["BTCUSDT", "BTCUSDT", "BTCUSDT"]
    assert storage.rows[0]["funding_rate"] == 0.0001
    assert storage.rows[1]["open_interest"] == 1_000_000_000
    assert storage.rows[2]["side"] == "long"
