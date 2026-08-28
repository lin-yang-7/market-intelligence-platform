import json

import pytest

from scripts.backfill_binance_market import (
    discover_active_usdt_symbols,
    load_completed,
    save_completed,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


class FakeHttpClient:
    def __init__(self):
        self.responses = [
            {"symbols": [
                {"symbol": "LOWUSDT", "status": "TRADING", "quoteAsset": "USDT"},
                {"symbol": "BTCUSDT", "status": "TRADING", "quoteAsset": "USDT"},
                {"symbol": "PAUSEDUSDT", "status": "BREAK", "quoteAsset": "USDT"},
                {"symbol": "ETHBTC", "status": "TRADING", "quoteAsset": "BTC"},
            ]},
            [{"symbol": "LOWUSDT", "quoteVolume": "3"}, {"symbol": "BTCUSDT", "quoteVolume": "10"}],
        ]

    async def get(self, _url, *, params=None):
        return FakeResponse(self.responses.pop(0))


@pytest.mark.asyncio
async def test_discovery_filters_and_sorts_active_usdt_symbols() -> None:
    assert await discover_active_usdt_symbols(FakeHttpClient()) == ["BTCUSDT", "LOWUSDT"]


def test_checkpoint_round_trip(tmp_path) -> None:
    path = tmp_path / "state.json"
    save_completed(path, {"ETHUSDT", "BTCUSDT"})

    assert load_completed(path) == {"BTCUSDT", "ETHUSDT"}
    assert json.loads(path.read_text(encoding="utf-8"))["completed"] == ["BTCUSDT", "ETHUSDT"]
