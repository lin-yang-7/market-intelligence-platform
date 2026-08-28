import asyncio

from mip_common.models import model_to_dict
from services.alert_service.app.repositories import InMemoryAlertRepository
from services.alert_service.app.services import AlertService
from services.ranking_service.app.schemas import RankingItem
from services.signal_service.app.repositories import InMemorySignalRepository
from services.signal_service.app.services import SignalService


async def main() -> None:
    signal_service = SignalService(InMemorySignalRepository())
    alert_service = AlertService(InMemoryAlertRepository())
    await alert_service.create_long_inflow_rule(
        conditions={"score": ">=90", "confidence": ">=0.9"},
        symbol="BTCUSDT",
        channel="sse",
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
    print([model_to_dict(item) for item in history])


if __name__ == "__main__":
    asyncio.run(main())
