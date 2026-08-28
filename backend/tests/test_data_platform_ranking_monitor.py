import pytest
from data_platform.app.processor import PipelineProcessor
from data_platform.app.schemas import PipelineEvent
from data_platform.app.storage import InMemoryEventStorage


@pytest.mark.asyncio
async def test_ranking_monitor_event_is_routed_and_stored() -> None:
    processor = PipelineProcessor()
    storage = InMemoryEventStorage()
    event = PipelineEvent(
        event_type="ranking.entered",
        timestamp=1700000000000,
        source="binance",
        data={
            "exchange": "binance",
            "symbol": "BTCUSDT",
            "rankingType": "opportunityBullish",
            "toRank": 1,
            "score": 72.5,
            "summary": {
                "marketBias": "uptrend",
                "btcStatus": "entered",
            },
        },
    )

    processed = processor.process(event)
    result = await storage.write(processed)

    assert processed.route.target_table == "ranking_monitor_event"
    assert result.stored is True
    assert storage.rows[0]["event_action"] == "entered"
    assert storage.rows[0]["ranking_type"] == "opportunityBullish"
    assert storage.rows[0]["to_rank"] == 1
    assert storage.rows[0]["score"] == 72.5
    assert storage.rows[0]["market_bias"] == "uptrend"


@pytest.mark.asyncio
async def test_ranking_strategy_event_is_stored_and_queryable() -> None:
    processor = PipelineProcessor()
    storage = InMemoryEventStorage()
    event = PipelineEvent(
        event_type="ranking.strategy",
        timestamp=1700000000000,
        source="binance",
        data={
            "exchange": "binance",
            "rankingType": "opportunityBullish",
            "event": "market_trend_up",
            "severity": "info",
            "symbol": "BTCUSDT",
            "title": "BTCUSDT entered opportunity bullish",
            "body": "BTC entered the opportunity monitor.",
            "summary": {"marketBias": "uptrend"},
        },
    )

    processed = processor.process(event)
    await storage.write(processed)
    events = await storage.list_ranking_monitor_events(ranking_type="opportunityBullish")

    assert processed.route.target_table == "ranking_monitor_event"
    assert events[0].eventAction == "market_trend_up"
    assert events[0].summary["title"] == "BTCUSDT entered opportunity bullish"
    assert events[0].summary["severity"] == "info"


def test_ranking_monitor_event_requires_symbol_and_ranking_type() -> None:
    processor = PipelineProcessor()
    event = PipelineEvent(
        event_type="ranking.exited",
        timestamp=1700000000000,
        source="binance",
        data={"symbol": "ETHUSDT"},
    )

    processed = processor.process(event)

    assert processed.quality.accepted is False
    assert processed.route.target_table == "event_dead_letter"
