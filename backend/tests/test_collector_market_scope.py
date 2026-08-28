from types import SimpleNamespace

import pytest
from services.collector_service.app.main import resolve_ticker_symbols


class DiscoveringConnector:
    async def fetch_top_usdt_symbols(self, limit: int) -> list[str]:
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT"][:limit]


@pytest.mark.asyncio
async def test_top_symbol_configuration_uses_discovery() -> None:
    settings = SimpleNamespace(collector_auto_top_symbols=2, collector_symbol_list=["BTCUSDT"])

    assert await resolve_ticker_symbols(DiscoveringConnector(), settings) == ["BTCUSDT", "ETHUSDT"]


@pytest.mark.asyncio
async def test_top_symbol_configuration_falls_back_when_connector_cannot_discover() -> None:
    settings = SimpleNamespace(collector_auto_top_symbols=10, collector_symbol_list=["BTCUSDT"])

    assert await resolve_ticker_symbols(object(), settings) == ["BTCUSDT"]
