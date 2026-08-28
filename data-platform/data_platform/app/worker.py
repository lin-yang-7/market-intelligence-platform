import asyncio
import logging
from typing import Any

from mip_common.config import get_settings
from mip_common.kafka import KafkaEventConsumer
from mip_common.models import validate_model

from .processor import PipelineProcessor, pipeline_processor
from .schemas import PipelineEvent, StorageResult
from .storage import EventStorage, create_event_storage

logger = logging.getLogger("data-platform")


def to_pipeline_event(event: dict[str, Any]) -> PipelineEvent:
    event_type = event.get("event_type") or event.get("event")
    data = event.get("data") or {}
    if not isinstance(data, dict):
        data = {"value": data}

    source = event.get("source") or event.get("exchange") or data.get("source") or "unknown"
    if event.get("exchange") and "exchange" not in data:
        data = {**data, "exchange": event["exchange"]}

    return validate_model(
        PipelineEvent,
        {
            "event_type": event_type,
            "timestamp": event.get("timestamp"),
            "source": source,
            "data": data,
        },
    )


async def handle_event(
    event: dict[str, Any],
    processor: PipelineProcessor | None = None,
    storage: EventStorage | None = None,
) -> StorageResult:
    processor = processor or pipeline_processor
    storage = storage or create_event_storage()
    processed = processor.process(to_pipeline_event(event))
    result = await storage.write(processed)
    logger.info(
        "processed event",
        extra={
            "event_type": processed.event.event_type,
            "target_table": result.target_table,
            "stored": result.stored,
        },
    )
    return result


async def consume_topic(topic: str) -> None:
    settings = get_settings()
    consumer = KafkaEventConsumer(
        topic=topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.data_platform_kafka_group_id,
    )

    async def handler(event: dict[str, Any]) -> None:
        await handle_event(event)

    await consumer.consume(handler)


async def consume_data_platform() -> None:
    settings = get_settings()
    await asyncio.gather(*(consume_topic(topic) for topic in settings.data_platform_topic_list))
