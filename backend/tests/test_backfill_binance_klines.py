from datetime import UTC, datetime

import pytest

from scripts.backfill_binance_klines import backfill_symbol, parse_kline, parse_timestamp


class FakeResponse:
    def __init__(self, rows):
        self.rows = rows

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.rows


class FakeHttpClient:
    def __init__(self, pages):
        self.pages = list(pages)
        self.params = []

    async def get(self, _url, *, params):
        self.params.append(params)
        return FakeResponse(self.pages.pop(0) if self.pages else [])


class FakeClickHouseClient:
    def __init__(self, existing=None):
        self.existing = existing or []
        self.inserted = []

    async def select(self, _query, _parameters):
        return [{"timestamp": timestamp} for timestamp in self.existing]

    async def insert(self, _table, rows):
        self.inserted.extend(rows)


def test_parse_timestamp_treats_naive_value_as_utc() -> None:
    assert parse_timestamp("2026-01-01T00:00:00") == int(
        datetime(2026, 1, 1, tzinfo=UTC).timestamp() * 1000
    )


def test_parse_kline_maps_binance_fields() -> None:
    kline = parse_kline([1_000, "1", "3", "0.5", "2", "10", 0, "15"], "btcusdt", "1m")

    assert kline.symbol == "BTCUSDT"
    assert kline.quoteVolume == 15.0


@pytest.mark.asyncio
async def test_backfill_inserts_only_missing_klines() -> None:
    first = [0, "1", "2", "0.5", "1.5", "10", 0, "15"]
    second = [60_000, "1.5", "3", "1", "2", "11", 0, "20"]
    http_client = FakeHttpClient([[first, second], []])
    clickhouse_client = FakeClickHouseClient(existing=["1970-01-01 00:00:00"])

    inserted = await backfill_symbol(
        http_client,
        clickhouse_client,
        "BTCUSDT",
        "1m",
        0,
        60_000,
    )

    assert inserted == 1
    assert [row["timestamp"] for row in clickhouse_client.inserted] == ["1970-01-01 00:01:00"]
    assert http_client.params[0]["limit"] == 1000
