import asyncio

from mip_common.events import MarketEvent
from mip_common.kafka import KafkaEventPublisher, deserialize_event
from mip_common.models import model_to_dict
from services.market_service.app.repositories import RedisTickerRepository


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str):
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.values[key] = value


class FakeProducer:
    def __init__(self) -> None:
        self.sent: list[tuple[str, bytes]] = []

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def send_and_wait(self, topic: str, payload: bytes) -> None:
        self.sent.append((topic, payload))


async def main() -> None:
    redis = FakeRedis()
    repository = RedisTickerRepository(redis)
    event = MarketEvent(
        event="market.ticker",
        exchange="binance",
        timestamp=1700000000000,
        data={"symbol": "BTCUSDT", "price": 68000},
    )
    await repository.save_ticker(event)
    ticker = await repository.get_ticker("BTCUSDT", "binance")

    producer = FakeProducer()
    publisher = KafkaEventPublisher("localhost:9092", producer_factory=lambda: producer)
    await publisher.publish("market.ticker", model_to_dict(event))

    print(model_to_dict(ticker) if ticker else None)
    print(deserialize_event(producer.sent[0][1]))


if __name__ == "__main__":
    asyncio.run(main())
