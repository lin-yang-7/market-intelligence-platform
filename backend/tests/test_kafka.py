import pytest
from mip_common.kafka import KafkaEventPublisher, deserialize_event, serialize_event

from .fakes import FakeKafkaProducer


def test_event_serialization_round_trip() -> None:
    event = {
        "event": "market.ticker",
        "exchange": "binance",
        "timestamp": 1700000000000,
        "data": {"symbol": "BTCUSDT", "price": 68000.0},
    }

    assert deserialize_event(serialize_event(event)) == event


@pytest.mark.asyncio
async def test_kafka_event_publisher_uses_producer_lifecycle() -> None:
    producer = FakeKafkaProducer()
    publisher = KafkaEventPublisher("localhost:9092", producer_factory=lambda: producer)
    event = {"event": "market.ticker", "exchange": "binance", "timestamp": 1, "data": {}}

    await publisher.publish("market.ticker", event)

    assert producer.started is True
    assert producer.stopped is True
    assert producer.sent[0][0] == "market.ticker"
    assert deserialize_event(producer.sent[0][1]) == event
