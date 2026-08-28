import asyncio

from mip_common.config import get_settings
from mip_common.events import MarketEvent
from mip_common.kafka import KafkaEventConsumer, deserialize_event
from mip_common.models import validate_model

from .dependencies import get_market_service


async def handle_payload(payload: bytes | str) -> None:
    event = validate_model(MarketEvent, deserialize_event(payload))
    await get_market_service().handle_market_event(event)


async def consume_topic(topic: str) -> None:
    settings = get_settings()
    consumer = KafkaEventConsumer(
        topic=topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="market-service",
    )

    async def handler(event: dict) -> None:
        market_event = validate_model(MarketEvent, event)
        await get_market_service().handle_market_event(market_event)

    await consumer.consume(handler)


async def consume_market_ticker() -> None:
    await consume_market_events()


async def consume_market_events() -> None:
    settings = get_settings()
    topics = [
        settings.kafka_topic_market_ticker,
        settings.kafka_topic_market_funding,
        settings.kafka_topic_market_open_interest,
        settings.kafka_topic_market_liquidation,
    ]
    await asyncio.gather(*(consume_topic(topic) for topic in topics))
