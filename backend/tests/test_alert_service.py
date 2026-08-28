import pytest
from services.alert_service.app.repositories import InMemoryAlertRepository
from services.alert_service.app.schemas import AlertCreateRequest
from services.alert_service.app.services import AlertService
from services.ranking_service.app.schemas import RankingItem
from services.signal_service.app.repositories import InMemorySignalRepository
from services.signal_service.app.services import SignalService


@pytest.mark.asyncio
async def test_alert_service_triggers_long_inflow_alert_from_signal() -> None:
    alert_service = AlertService(InMemoryAlertRepository())
    signal_service = SignalService(InMemorySignalRepository())
    await alert_service.create_rule(
        AlertCreateRequest(
            type="longInflow",
            symbol="BTCUSDT",
            conditions={"score": ">=90", "confidence": ">=0.9"},
            channel="sse",
        )
    )
    signals = await signal_service.generate_from_ranking(
        "longInflow",
        [
            RankingItem(
                rank=1,
                symbol="BTCUSDT",
                exchange="binance",
                score=95.0,
                confidence=1.0,
                timestamp=1700000000000,
                factors={
                    "long_inflow_score": 95.0,
                    "volume_activity": 90.0,
                    "price_momentum": 5.0,
                },
            )
        ],
    )

    history = await alert_service.evaluate_signal(signals[0])

    assert len(history) == 1
    assert history[0].symbol == "BTCUSDT"
    assert history[0].result == "success"


@pytest.mark.asyncio
async def test_alert_service_rejects_invalid_condition() -> None:
    alert_service = AlertService(InMemoryAlertRepository())

    with pytest.raises(Exception) as exc_info:
        await alert_service.create_rule(
            AlertCreateRequest(
                type="longInflow",
                conditions={"score": "high"},
                channel="sse",
            )
        )

    assert exc_info.value.code == 7002
