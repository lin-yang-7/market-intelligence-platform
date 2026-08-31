import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any


def serialize_event(event: dict[str, Any]) -> bytes:
    return json.dumps(event, separators=(",", ":"), sort_keys=True).encode("utf-8")


def deserialize_event(payload: bytes | str) -> dict[str, Any]:
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    decoded = json.loads(payload)
    if not isinstance(decoded, dict):
        raise ValueError("Kafka event payload must be a JSON object")
    return decoded


class InMemoryEventBus:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def publish(self, event: dict[str, Any]) -> None:
        self.events.append(event)

    async def replay(self, handler: Callable[[dict[str, Any]], Any]) -> None:
        for event in self.events:
            result = handler(event)
            if hasattr(result, "__await__"):
                await result


class KafkaEventPublisher:
    def __init__(self, bootstrap_servers: str, producer_factory=None) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.producer_factory = producer_factory

    async def publish(self, topic: str, event: dict[str, Any]) -> None:
        producer = self._create_producer()
        await producer.start()
        try:
            await producer.send_and_wait(topic, serialize_event(event))
        finally:
            await producer.stop()

    def _create_producer(self):
        if self.producer_factory is not None:
            return self.producer_factory()

        from aiokafka import AIOKafkaProducer

        return AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)


class KafkaEventConsumer:
    def __init__(
        self,
        topic: str,
        bootstrap_servers: str,
        group_id: str,
        consumer_factory=None,
    ) -> None:
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer_factory = consumer_factory

    async def consume(self, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        # Compose only guarantees start order.  Kafka can still be starting
        # while consumer containers are launched, so keep consumers alive and
        # retry bootstrap rather than exiting permanently on a cold start.
        from aiokafka.errors import KafkaConnectionError

        while True:
            consumer = self._create_consumer()
            try:
                await consumer.start()
                async for message in consumer:
                    await handler(deserialize_event(message.value))
                    await consumer.commit()
            except KafkaConnectionError:
                logging.getLogger(__name__).warning(
                    "Kafka is not ready for topic %s; retrying in 5 seconds",
                    self.topic,
                )
            finally:
                await consumer.stop()
            await asyncio.sleep(5)

    def _create_consumer(self):
        if self.consumer_factory is not None:
            return self.consumer_factory()

        from aiokafka import AIOKafkaConsumer

        return AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            enable_auto_commit=False,
        )
