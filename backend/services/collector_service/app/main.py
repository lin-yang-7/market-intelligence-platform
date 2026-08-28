import asyncio
import logging

from mip_common.config import get_settings
from mip_common.models import model_to_dict

from .connectors import create_ticker_connector
from .publisher import KafkaPublisher

logger = logging.getLogger("collector-service")


async def resolve_ticker_symbols(connector, settings) -> list[str]:
    if settings.collector_auto_top_symbols <= 0:
        return settings.collector_symbol_list
    discover = getattr(connector, "fetch_top_usdt_symbols", None)
    if discover is None:
        logger.warning("top-symbol discovery is unavailable; using configured symbols")
        return settings.collector_symbol_list
    return await discover(settings.collector_auto_top_symbols)


async def resolve_derivative_symbols(connector, settings) -> list[str]:
    if settings.collector_derivatives_top_symbols <= 0:
        return settings.collector_symbol_list
    discover = getattr(connector, "fetch_top_usdt_symbols", None)
    if discover is None:
        logger.warning("derivatives discovery is unavailable; using configured symbols")
        return settings.collector_symbol_list
    return await discover(settings.collector_derivatives_top_symbols)


async def run_once(include_derivatives: bool = True) -> None:
    settings = get_settings()
    connector = create_ticker_connector(settings.collector_exchange)
    publisher = KafkaPublisher()
    for symbol in await resolve_ticker_symbols(connector, settings):
        ticker = await connector.fetch_ticker(symbol)
        await publisher.publish_market_event(model_to_dict(ticker))
        logger.info("published ticker", extra={"symbol": symbol, "exchange": ticker.exchange})

    if not include_derivatives:
        return
    for symbol in await resolve_derivative_symbols(connector, settings):
        funding = await connector.fetch_funding(symbol)
        await publisher.publish_market_event(model_to_dict(funding))
        logger.info("published funding", extra={"symbol": symbol, "exchange": funding.exchange})

        open_interest = await connector.fetch_open_interest(symbol)
        await publisher.publish_market_event(model_to_dict(open_interest))
        logger.info(
            "published open interest",
            extra={"symbol": symbol, "exchange": open_interest.exchange},
        )

        for liquidation in await connector.fetch_liquidations(symbol):
            await publisher.publish_market_event(model_to_dict(liquidation))
            logger.info(
                "published liquidation",
                extra={"symbol": symbol, "exchange": liquidation.exchange},
            )
        if settings.collector_derivative_request_delay_seconds:
            await asyncio.sleep(settings.collector_derivative_request_delay_seconds)


async def run_forever() -> None:
    settings = get_settings()
    last_derivatives_at = 0.0
    while True:
        try:
            now = asyncio.get_running_loop().time()
            include_derivatives = (
                now - last_derivatives_at >= settings.collector_derivatives_interval_seconds
            )
            await run_once(include_derivatives=include_derivatives)
            if include_derivatives:
                last_derivatives_at = now
        except Exception:
            logger.exception("collector cycle failed")
        await asyncio.sleep(settings.collector_interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=get_settings().log_level)
    asyncio.run(run_forever())
