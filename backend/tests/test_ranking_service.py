import pytest
from mip_common.events import MarketEvent
from services.feature_service.app.repositories import InMemoryFeatureRepository
from services.feature_service.app.services import FeatureService
from services.ranking_service.app.services import RankingService


@pytest.mark.asyncio
async def test_ranking_service_generates_ordered_long_inflow_ranking() -> None:
    repository = InMemoryFeatureRepository()
    feature_service = FeatureService(repository)
    ranking_service = RankingService(repository)

    await feature_service.calculate_from_market_ticker(
        MarketEvent(
            event="market.ticker",
            exchange="binance",
            timestamp=1700000000000,
            data={"symbol": "BTCUSDT", "price": 68000, "change24h": 2.5, "volume24h": 120000000},
        )
    )
    await feature_service.calculate_from_market_ticker(
        MarketEvent(
            event="market.ticker",
            exchange="binance",
            timestamp=1700000001000,
            data={"symbol": "ETHUSDT", "price": 3500, "change24h": 1.0, "volume24h": 5000000},
        )
    )

    ranking = await ranking_service.get_ranking("longInflow", exchange="binance", limit=10)

    assert [item.symbol for item in ranking] == ["BTCUSDT", "ETHUSDT"]
    assert ranking[0].rank == 1
    assert ranking[0].score > ranking[1].score


@pytest.mark.asyncio
async def test_ranking_monitor_reports_entered_exited_and_moved() -> None:
    repository = InMemoryFeatureRepository()
    feature_service = FeatureService(repository)
    ranking_service = RankingService(repository)

    await feature_service.calculate_from_market_ticker(
        MarketEvent(
            event="market.ticker",
            exchange="binance",
            timestamp=1700000000000,
            data={"symbol": "AAAUSDT", "price": 10, "change24h": 8, "volume24h": 200000000},
        )
    )
    await feature_service.calculate_from_market_ticker(
        MarketEvent(
            event="market.ticker",
            exchange="binance",
            timestamp=1700000000000,
            data={"symbol": "BBBUSDT", "price": 10, "change24h": 6, "volume24h": 160000000},
        )
    )

    first = await ranking_service.monitor_ranking(
        "opportunityBullish",
        exchange="binance",
        limit=10,
        min_score=50,
        max_score=100,
    )

    assert [item.symbol for item in first.changes.entered] == ["AAAUSDT", "BBBUSDT"]
    assert first.changes.exited == []

    await feature_service.calculate_from_market_ticker(
        MarketEvent(
            event="market.ticker",
            exchange="binance",
            timestamp=1700000001000,
            data={"symbol": "AAAUSDT", "price": 10, "change24h": -1, "volume24h": 1000000},
        )
    )
    await feature_service.calculate_from_market_ticker(
        MarketEvent(
            event="market.ticker",
            exchange="binance",
            timestamp=1700000001000,
            data={"symbol": "BBBUSDT", "price": 10, "change24h": 9, "volume24h": 240000000},
        )
    )
    await feature_service.calculate_from_market_ticker(
        MarketEvent(
            event="market.ticker",
            exchange="binance",
            timestamp=1700000001000,
            data={"symbol": "CCCUSDT", "price": 10, "change24h": 7, "volume24h": 180000000},
        )
    )

    second = await ranking_service.monitor_ranking(
        "opportunityBullish",
        exchange="binance",
        limit=10,
        min_score=50,
        max_score=100,
    )

    assert [item.symbol for item in second.changes.entered] == ["CCCUSDT"]
    assert [item.symbol for item in second.changes.exited] == ["AAAUSDT"]
    assert second.changes.moved[0].symbol == "BBBUSDT"
    assert second.changes.moved[0].fromRank == 2
    assert second.changes.moved[0].toRank == 1


@pytest.mark.asyncio
async def test_opportunity_monitor_defaults_to_valuescan_score_band_and_btc_bias() -> None:
    repository = InMemoryFeatureRepository()
    feature_service = FeatureService(repository)
    ranking_service = RankingService(repository)

    await feature_service.calculate_from_market_ticker(
        MarketEvent(
            event="market.ticker",
            exchange="binance",
            timestamp=1700000000000,
            data={"symbol": "BTCUSDT", "price": 68000, "change24h": 5, "volume24h": 100000000},
        )
    )
    await feature_service.calculate_from_market_ticker(
        MarketEvent(
            event="market.ticker",
            exchange="binance",
            timestamp=1700000000000,
            data={"symbol": "FOMOUSDT", "price": 10, "change24h": 12, "volume24h": 300000000},
        )
    )

    snapshot = await ranking_service.monitor_ranking(
        "opportunityBullish",
        exchange="binance",
        limit=10,
    )

    assert [item.symbol for item in snapshot.active] == ["BTCUSDT"]
    assert snapshot.active[0].strategyState == "steady_trend_candidate"
    assert snapshot.active[0].signalColor == "green"
    assert snapshot.summary["scoreBand"] == {"min": 55.0, "max": 80.0}
    assert snapshot.summary["btcStatus"] == "entered"
    assert snapshot.summary["marketBias"] == "uptrend"
    assert snapshot.changes.strategyEvents[0].event == "market_trend_up"
    assert snapshot.changes.strategyEvents[0].symbol == "BTCUSDT"


@pytest.mark.asyncio
async def test_abnormal_bullish_item_exposes_fomo_strategy_view() -> None:
    repository = InMemoryFeatureRepository()
    feature_service = FeatureService(repository)
    ranking_service = RankingService(repository)

    await feature_service.calculate_from_market_ticker(
        MarketEvent(
            event="market.ticker",
            exchange="binance",
            timestamp=1700000000000,
            data={"symbol": "FOMOUSDT", "price": 10, "change24h": 12, "volume24h": 300000000},
        )
    )

    ranking = await ranking_service.get_ranking("abnormalBullish", exchange="binance", limit=10)

    assert ranking[0].score == 100
    assert ranking[0].strategyState == "fomo_watch"
    assert ranking[0].signalColor == "orange"
    assert "fomo_risk" in ranking[0].reasonTags


@pytest.mark.asyncio
async def test_risk_bearish_score_uses_derivatives_pressure() -> None:
    repository = InMemoryFeatureRepository()
    feature_service = FeatureService(repository)
    ranking_service = RankingService(repository)

    await feature_service.calculate_from_market_ticker(
        MarketEvent(
            event="market.ticker",
            exchange="binance",
            timestamp=1700000000000,
            data={"symbol": "RISKUSDT", "price": 10, "change24h": -4, "volume24h": 100000000},
        )
    )
    await feature_service.calculate_from_derivatives(
        symbol="RISKUSDT",
        exchange="binance",
        timestamp=1700000001000,
        funding_rate=0.001,
        open_interest_change=40,
        long_liquidation_value=500000,
        taker_sell_value=500000,
    )

    ranking = await ranking_service.get_ranking("riskBearish", exchange="binance", limit=10)

    assert ranking[0].symbol == "RISKUSDT"
    assert ranking[0].score >= 55
    assert ranking[0].strategyState in {"bearish_risk_watch", "high_dump_risk"}
    assert ranking[0].signalColor in {"orange", "red"}
    assert "derivatives_pressure" in ranking[0].reasonTags


@pytest.mark.asyncio
async def test_risk_bearish_monitor_flags_batch_risk() -> None:
    repository = InMemoryFeatureRepository()
    feature_service = FeatureService(repository)
    ranking_service = RankingService(repository)

    for index in range(5):
        await feature_service.calculate_from_market_ticker(
            MarketEvent(
                event="market.ticker",
                exchange="binance",
                timestamp=1700000000000 + index,
                data={
                    "symbol": f"RISK{index}USDT",
                    "price": 10,
                    "change24h": -8,
                    "volume24h": 120000000,
                },
            )
        )

    snapshot = await ranking_service.monitor_ranking(
        "riskBearish",
        exchange="binance",
        limit=10,
    )

    assert len(snapshot.changes.entered) == 5
    assert snapshot.summary["batchRisk"] is True
    assert snapshot.summary["marketBias"] == "selloff_risk"
    assert snapshot.changes.strategyEvents[0].event == "batch_risk_bearish"
    assert snapshot.changes.strategyEvents[0].severity == "critical"


@pytest.mark.asyncio
async def test_opportunity_monitor_emits_tracking_ended_and_market_reversal_events() -> None:
    repository = InMemoryFeatureRepository()
    feature_service = FeatureService(repository)
    ranking_service = RankingService(repository)

    for symbol in ("BTCUSDT", "ETHUSDT"):
        await feature_service.calculate_from_market_ticker(
            MarketEvent(
                event="market.ticker",
                exchange="binance",
                timestamp=1700000000000,
                data={"symbol": symbol, "price": 10, "change24h": 5, "volume24h": 100000000},
            )
        )

    await ranking_service.monitor_ranking("opportunityBullish", exchange="binance", limit=10)

    for symbol in ("BTCUSDT", "ETHUSDT"):
        await feature_service.calculate_from_market_ticker(
            MarketEvent(
                event="market.ticker",
                exchange="binance",
                timestamp=1700000001000,
                data={"symbol": symbol, "price": 10, "change24h": -2, "volume24h": 1000000},
            )
        )

    snapshot = await ranking_service.monitor_ranking(
        "opportunityBullish",
        exchange="binance",
        limit=10,
        min_score=1,
    )

    event_names = [event.event for event in snapshot.changes.strategyEvents]

    assert "market_trend_reversal_watch" in event_names
    assert "major_coin_exited" in event_names
    assert "high_risk_sell_interpretation" in event_names
    assert event_names.count("tracking_ended") == 2
