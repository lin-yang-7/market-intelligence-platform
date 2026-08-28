import asyncio

from mip_common.models import model_to_dict
from services.collector_service.app.connectors import create_ticker_connector


async def main() -> None:
    connector = create_ticker_connector("mock")
    event = await connector.fetch_ticker("BTCUSDT")
    print(model_to_dict(event))
    print(model_to_dict(await connector.fetch_funding("BTCUSDT")))
    print(model_to_dict(await connector.fetch_open_interest("BTCUSDT")))
    for liquidation in await connector.fetch_liquidations("BTCUSDT"):
        print(model_to_dict(liquidation))


if __name__ == "__main__":
    asyncio.run(main())
