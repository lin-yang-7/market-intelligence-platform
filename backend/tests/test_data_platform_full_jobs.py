from pathlib import Path

from data_platform.app.jobs import (
    BatchPipelineJob,
    DataFreshnessMonitor,
    GovernanceCatalog,
    LocalDataLake,
    StreamProcessingJob,
    WarehousePlanner,
)
from data_platform.app.main import app
from data_platform.app.schemas import PipelineEvent
from fastapi.testclient import TestClient
from mip_common.responses import now_ms


def sample_events(current: int | None = None) -> list[PipelineEvent]:
    base = current or 1_700_000_000_000
    return [
        PipelineEvent(
            event_type="market.ticker",
            timestamp=base,
            source="binance",
            data={"symbol": "BTCUSDT", "price": 68000, "volume": 1000},
        ),
        PipelineEvent(
            event_type="market.ticker",
            timestamp=base + 10_000,
            source="binance",
            data={"symbol": "BTCUSDT", "price": 68100, "volume": 1200},
        ),
        PipelineEvent(
            event_type="feature.updated",
            timestamp=base + 20_000,
            source="feature-service",
            data={"symbol": "BTCUSDT", "feature": "momentum", "value": 1.5},
        ),
        PipelineEvent(
            event_type="ranking.entered",
            timestamp=base + 30_000,
            source="ranking-service",
            data={"symbol": "BTCUSDT", "rankingType": "opportunityBullish"},
        ),
    ]


def test_stream_processing_job_aggregates_window() -> None:
    result = StreamProcessingJob().run(sample_events(), window_ms=60_000)
    ticker = next(row for row in result if row.eventType == "market.ticker")

    assert ticker.symbol == "BTCUSDT"
    assert ticker.eventCount == 2
    assert ticker.avgPrice == 68050
    assert ticker.totalVolume == 2200


def test_batch_pipeline_job_rolls_up_symbol_features() -> None:
    result = BatchPipelineJob().run(sample_events(), "daily_feature_rollup")

    assert result.inputEvents == 4
    assert result.outputRows == 1
    assert result.symbols == ["BTCUSDT"]
    assert result.featureRows[0]["eventCount"] == 4


def test_warehouse_planner_returns_four_layers() -> None:
    plan = WarehousePlanner().plan(sample_events())

    assert [layer.name for layer in plan.layers] == ["raw", "detail", "feature", "analysis"]
    assert "ods_market_event" in plan.layers[0].tables
    assert "ads_ranking_monitor" in plan.layers[3].tables


def test_local_data_lake_writes_partitioned_jsonl(tmp_path: Path) -> None:
    manifest = LocalDataLake(tmp_path).write(sample_events(), "raw_events")

    assert manifest.rowCount == 4
    assert manifest.partitions
    assert all(Path(file).is_file() for file in manifest.files)


def test_freshness_monitor_reports_missing_and_stale_symbols() -> None:
    current = now_ms()
    events = sample_events(current - 600_000)
    report = DataFreshnessMonitor().report(
        events,
        expected_symbols=["BTCUSDT", "ETHUSDT"],
        max_delay_ms=300_000,
        expected_interval_ms=60_000,
    )

    assert report.status == "degraded"
    assert report.staleEvents == 1
    assert report.missingSymbols == ["ETHUSDT"]
    assert report.eventLossSuspicions[0]["symbol"] == "BTCUSDT"


def test_governance_catalog_builds_lineage_graph() -> None:
    report = GovernanceCatalog().report(sample_events())

    assert report.owners["market_ticker"] == "data-platform"
    assert report.owners["ranking_monitor_event"] == "ranking-service"
    assert any(edge.relation == "routes_to" for edge in report.edges)


def test_data_platform_full_api_endpoints() -> None:
    client = TestClient(app)
    events = [event.model_dump() for event in sample_events()]

    stream = client.post("/v1/data/stream/process", json={"events": events, "windowMs": 60000})
    batch = client.post(
        "/v1/data/batch/run",
        json={"events": events, "jobName": "daily_feature_rollup"},
    )
    warehouse = client.post("/v1/data/warehouse/plan", json={"events": events})
    freshness = client.post(
        "/v1/data/freshness/report",
        json={
            "events": events,
            "expectedSymbols": ["BTCUSDT"],
            "maxDelayMs": 999999999999,
            "expectedIntervalMs": 60000,
        },
    )
    lineage = client.post("/v1/data/governance/lineage", json={"events": events})

    assert stream.status_code == 200
    assert batch.json()["data"]["outputRows"] == 1
    assert len(warehouse.json()["data"]["layers"]) == 4
    assert freshness.json()["data"]["missingSymbols"] == []
    assert lineage.json()["data"]["nodes"]
