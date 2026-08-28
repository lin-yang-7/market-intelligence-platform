import pytest
from mip_common.kafka import deserialize_event
from mip_common.models import model_to_dict
from services.collector_service.app.connectors import create_ticker_connector
from services.collector_service.app.publisher import KafkaPublisher

from .fakes import FakeKafkaProducer


@pytest.mark.asyncio
async def test_mock_collector_fetches_derivatives_events() -> None:
    connector = create_ticker_connector("mock")

    funding = await connector.fetch_funding("BTCUSDT")
    open_interest = await connector.fetch_open_interest("BTCUSDT")
    liquidations = await connector.fetch_liquidations("BTCUSDT")

    assert funding.event == "market.funding"
    assert funding.data["fundingRate"] == 0.0001
    assert open_interest.event == "market.open_interest"
    assert open_interest.data["openInterest"] == 1_000_000_000
    assert liquidations[0].event == "market.liquidation"
    assert liquidations[0].data["value"] == 100500


@pytest.mark.asyncio
async def test_collector_publisher_routes_derivatives_topics() -> None:
    producer = FakeKafkaProducer()

    def producer_factory():
        return producer

    publisher = KafkaPublisher()
    publisher.publisher.producer_factory = producer_factory
    connector = create_ticker_connector("mock")
    events = [
        await connector.fetch_ticker("BTCUSDT"),
        await connector.fetch_funding("BTCUSDT"),
        await connector.fetch_open_interest("BTCUSDT"),
        *(await connector.fetch_liquidations("BTCUSDT")),
    ]

    for event in events:
        await publisher.publish_market_event(model_to_dict(event))

    topics = [topic for topic, _payload in producer.sent]
    payloads = [deserialize_event(payload) for _topic, payload in producer.sent]

    assert topics == [
        "market.ticker",
        "market.funding",
        "market.open_interest",
        "market.liquidation",
    ]
    assert [payload["event"] for payload in payloads] == topics
