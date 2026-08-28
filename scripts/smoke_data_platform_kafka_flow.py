import asyncio

from data_platform.app.processor import PipelineProcessor
from data_platform.app.storage import InMemoryEventStorage
from data_platform.app.worker import handle_event
from mip_common.models import model_to_dict
from mip_common.responses import now_ms


async def main() -> None:
    storage = InMemoryEventStorage()
    event = {
        "event": "market.ticker",
        "exchange": "binance",
        "timestamp": now_ms(),
        "data": {
            "symbol": "ETHUSDT",
            "price": 3500,
            "change24h": 1.8,
            "volume24h": 86000000,
        },
    }
    result = await handle_event(event, PipelineProcessor(), storage)
    print(model_to_dict(result))
    print(storage.rows)


if __name__ == "__main__":
    asyncio.run(main())
