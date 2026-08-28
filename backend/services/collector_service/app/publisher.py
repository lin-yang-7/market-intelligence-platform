from mip_common.config import get_settings
from mip_common.kafka import KafkaEventPublisher


class KafkaPublisher:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.publisher = KafkaEventPublisher(self.settings.kafka_bootstrap_servers)

    async def publish_market_ticker(self, event: dict) -> None:
        await self.publisher.publish(self.settings.kafka_topic_market_ticker, event)

    async def publish_market_funding(self, event: dict) -> None:
        await self.publisher.publish(self.settings.kafka_topic_market_funding, event)

    async def publish_market_open_interest(self, event: dict) -> None:
        await self.publisher.publish(self.settings.kafka_topic_market_open_interest, event)

    async def publish_market_liquidation(self, event: dict) -> None:
        await self.publisher.publish(self.settings.kafka_topic_market_liquidation, event)

    async def publish_market_event(self, event: dict) -> None:
        event_type = event.get("event")
        if event_type == "market.ticker":
            await self.publish_market_ticker(event)
            return
        if event_type == "market.funding":
            await self.publish_market_funding(event)
            return
        if event_type == "market.open_interest":
            await self.publish_market_open_interest(event)
            return
        if event_type == "market.liquidation":
            await self.publish_market_liquidation(event)
            return
        raise ValueError(f"Unsupported market event type: {event_type}")
