import asyncio

from mip_common.history import ClickHouseFeatureHistoryRepository
from mip_common.models import model_to_dict
from services.feature_service.app.schemas import FeatureValue


class FakeClickHouseClient:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    async def insert(self, table: str, rows: list[dict]) -> None:
        self.rows.extend(rows)

    async def select(self, query: str, parameters: dict) -> list[dict]:
        return [
            row
            for row in self.rows
            if row["symbol"] == parameters["symbol"]
            and row["feature_name"] == parameters["feature"]
        ]


async def main() -> None:
    repository = ClickHouseFeatureHistoryRepository(FakeClickHouseClient())
    await repository.save_features(
        [
            FeatureValue(
                symbol="BTCUSDT",
                exchange="binance",
                feature="price_momentum",
                value=2.5,
                timestamp=1700000000000,
            )
        ]
    )
    values = await repository.list_history(FeatureValue, "BTCUSDT", "price_momentum", "binance")
    print([model_to_dict(value) for value in values])


if __name__ == "__main__":
    asyncio.run(main())
