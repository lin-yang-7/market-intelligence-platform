from types import SimpleNamespace

import pytest
from services.collector_service.app.main import resolve_derivative_symbols


class DiscoveringConnector:
    async def fetch_top_usdt_symbols(self, limit: int) -> list[str]:
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT"][:limit]


@pytest.mark.asyncio
async def test_derivative_scope_uses_top_symbols_when_configured() -> None:
    settings = SimpleNamespace(
        collector_derivatives_top_symbols=2,
        collector_symbol_list=["BTCUSDT"],
    )

    assert await resolve_derivative_symbols(DiscoveringConnector(), settings) == [
        "BTCUSDT",
        "ETHUSDT",
    ]


@pytest.mark.asyncio
async def test_derivative_scope_defaults_to_explicit_symbols() -> None:
    settings = SimpleNamespace(
        collector_derivatives_top_symbols=0,
        collector_symbol_list=["BTCUSDT"],
    )

    assert await resolve_derivative_symbols(object(), settings) == ["BTCUSDT"]
