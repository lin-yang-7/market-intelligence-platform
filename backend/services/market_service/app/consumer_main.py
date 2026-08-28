import asyncio
import logging

from mip_common.config import get_settings

from .worker import consume_market_events

if __name__ == "__main__":
    logging.basicConfig(level=get_settings().log_level)
    asyncio.run(consume_market_events())
