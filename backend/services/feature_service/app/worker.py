import asyncio

from mip_common.config import get_settings
from mip_common.events import MarketEvent
from mip_common.kafka import KafkaEventConsumer, KafkaEventPublisher, deserialize_event
from mip_common.models import model_to_dict, validate_model

from .dependencies import get_feature_service
from .schemas import FeatureValue


async def handle_payload(payload: bytes | str) -> list[FeatureValue]:
    event = validate_model(MarketEvent, deserialize_event(payload))
    return await handle_event(model_to_dict(event))


async def handle_event(event: dict) -> list[FeatureValue]:
    market_event = validate_model(MarketEvent, event)
    features = await get_feature_service().calculate_from_market_event(market_event)
    await publish_feature_updates(features)
    return features


async def publish_feature_updates(features: list[FeatureValue]) -> None:
    if not features:
        return
    settings = get_settings()
    publisher = KafkaEventPublisher(settings.kafka_bootstrap_servers)
    for feature in features:
        await publisher.publish(
            settings.kafka_topic_feature_updated,
            {
                "event_type": "feature.updated",
                "timestamp": feature.timestamp,
                "source": feature.exchange,
                "data": {
                    "exchange": feature.exchange,
                    "symbol": feature.symbol,
                    "feature": feature.feature,
                    "value": feature.value,
                    "version": feature.version,
                },
            },
        )


async def consume_topic(topic: str) -> None:
    settings = get_settings()
    consumer = KafkaEventConsumer(
        topic=topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="feature-service",
    )
    await consumer.consume(handle_event)


async def consume_feature_events() -> None:
    settings = get_settings()
    topics = [
        settings.kafka_topic_market_ticker,
        settings.kafka_topic_market_funding,
        settings.kafka_topic_market_open_interest,
        settings.kafka_topic_market_liquidation,
        "market.trade",
    ]
    await asyncio.gather(*(consume_topic(topic) for topic in topics))
