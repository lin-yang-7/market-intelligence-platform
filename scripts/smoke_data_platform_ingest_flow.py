import asyncio

from data_platform.app.processor import PipelineProcessor
from data_platform.app.schemas import PipelineEvent
from data_platform.app.storage import InMemoryEventStorage
from mip_common.models import model_to_dict
from mip_common.responses import now_ms


async def main() -> None:
    processor = PipelineProcessor()
    storage = InMemoryEventStorage()
    event = PipelineEvent(
        event_type="market.ticker",
        timestamp=now_ms(),
        source="binance",
        data={
            "exchange": "binance",
            "symbol": "btcusdt",
            "price": 68000,
            "change24h": 2.4,
            "volume24h": 120000000,
        },
    )
    processed = processor.process(event)
    result = await storage.write(processed)
    print(model_to_dict(processed))
    print(model_to_dict(result))


if __name__ == "__main__":
    asyncio.run(main())
