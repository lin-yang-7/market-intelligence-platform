import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from mip_common.responses import now_ms

from .processor import PipelineProcessor
from .router import TABLE_BY_EVENT_TYPE
from .schemas import (
    BatchPipelineResult,
    DataFreshnessReport,
    DataLakeManifest,
    GovernanceReport,
    LineageEdge,
    LineageNode,
    PipelineEvent,
    StreamWindowResult,
    WarehouseLayer,
    WarehousePlan,
)

WAREHOUSE_LAYER_BY_EVENT_TYPE = {
    "market.ticker": ("ods_market_event", "dwd_market_ticker", "dws_market_symbol_window"),
    "market.kline": ("ods_market_event", "dwd_market_kline", "dws_market_symbol_window"),
    "market.trade": ("ods_market_event", "dwd_market_trade", "dws_market_symbol_window"),
    "market.funding": ("ods_derivatives_event", "dwd_funding_rate", "dws_derivatives_symbol"),
    "market.open_interest": (
        "ods_derivatives_event",
        "dwd_open_interest",
        "dws_derivatives_symbol",
    ),
    "market.liquidation": ("ods_derivatives_event", "dwd_liquidation", "dws_derivatives_symbol"),
    "feature.updated": ("ods_feature_event", "dwd_feature_value", "ads_feature_snapshot"),
    "ranking.updated": ("ods_ranking_event", "dwd_ranking_score", "ads_ranking_monitor"),
    "ranking.entered": ("ods_ranking_event", "dwd_ranking_lifecycle", "ads_ranking_monitor"),
    "ranking.exited": ("ods_ranking_event", "dwd_ranking_lifecycle", "ads_ranking_monitor"),
    "ranking.moved": ("ods_ranking_event", "dwd_ranking_lifecycle", "ads_ranking_monitor"),
    "ranking.strategy": ("ods_ranking_event", "dwd_ranking_strategy", "ads_ranking_monitor"),
    "signal.created": ("ods_signal_event", "dwd_signal_record", "ads_signal_timeline"),
}

OWNER_BY_DOMAIN = {
    "market": "data-platform",
    "feature": "feature-service",
    "ranking": "ranking-service",
    "signal": "signal-service",
    "alert": "notification-service",
}


class StreamProcessingJob:
    def __init__(self, processor: PipelineProcessor | None = None) -> None:
        self.processor = processor or PipelineProcessor()

    def run(self, events: list[PipelineEvent], window_ms: int) -> list[StreamWindowResult]:
        grouped: dict[tuple[str, str, int], list[tuple[PipelineEvent, bool]]] = defaultdict(list)
        for event in events:
            symbol = str(event.data.get("symbol", "market")).upper()
            window_start = event.timestamp // window_ms * window_ms
            quality = self.processor.validate(event)
            grouped[(event.event_type, symbol, window_start)].append((event, quality.accepted))

        results: list[StreamWindowResult] = []
        for (event_type, symbol, window_start), rows in sorted(grouped.items()):
            prices = [_float_or_zero(event.data.get("price")) for event, _accepted in rows]
            prices = [price for price in prices if price > 0]
            volumes = [
                _float_or_zero(event.data.get("volume", event.data.get("quantity", 0.0)))
                for event, _accepted in rows
            ]
            results.append(
                StreamWindowResult(
                    eventType=event_type,
                    symbol=symbol,
                    windowStart=window_start,
                    windowEnd=window_start + window_ms,
                    eventCount=len(rows),
                    minPrice=min(prices, default=0.0),
                    maxPrice=max(prices, default=0.0),
                    avgPrice=round(sum(prices) / len(prices), 8) if prices else 0.0,
                    totalVolume=round(sum(volumes), 8),
                    acceptedEvents=sum(1 for _event, accepted in rows if accepted),
                    rejectedEvents=sum(1 for _event, accepted in rows if not accepted),
                )
            )
        return results


class BatchPipelineJob:
    def run(self, events: list[PipelineEvent], job_name: str) -> BatchPipelineResult:
        by_symbol: dict[str, list[PipelineEvent]] = defaultdict(list)
        for event in events:
            if "symbol" in event.data:
                by_symbol[str(event.data["symbol"]).upper()].append(event)

        feature_rows: list[dict[str, Any]] = []
        for symbol, rows in sorted(by_symbol.items()):
            prices = [
                _float_or_zero(row.data.get("price", row.data.get("close", 0.0)))
                for row in rows
            ]
            prices = [price for price in prices if price > 0]
            volumes = [
                _float_or_zero(row.data.get("volume", row.data.get("quantity", 0.0)))
                for row in rows
            ]
            feature_rows.append(
                {
                    "symbol": symbol,
                    "eventCount": len(rows),
                    "avgPrice": round(sum(prices) / len(prices), 8) if prices else 0.0,
                    "totalVolume": round(sum(volumes), 8),
                    "firstTimestamp": min(row.timestamp for row in rows),
                    "lastTimestamp": max(row.timestamp for row in rows),
                }
            )
        return BatchPipelineResult(
            jobName=job_name,
            inputEvents=len(events),
            outputRows=len(feature_rows),
            symbols=sorted(by_symbol),
            featureRows=feature_rows,
        )


class WarehousePlanner:
    def plan(self, events: list[PipelineEvent]) -> WarehousePlan:
        layer_tables: dict[str, set[str]] = {
            "raw": set(),
            "detail": set(),
            "feature": set(),
            "analysis": set(),
        }
        accepted = 0
        for event in events:
            layers = WAREHOUSE_LAYER_BY_EVENT_TYPE.get(event.event_type)
            if not layers:
                continue
            accepted += 1
            raw, detail, analysis = layers
            layer_tables["raw"].add(raw)
            layer_tables["detail"].add(detail)
            if event.event_type == "feature.updated":
                layer_tables["feature"].add("feature_history")
            layer_tables["analysis"].add(analysis)

        return WarehousePlan(
            layers=[
                WarehouseLayer(
                    name="raw",
                    purpose="Store original source events for replay and audit.",
                    tables=sorted(layer_tables["raw"]),
                    inputEvents=len(events),
                    outputRows=accepted,
                ),
                WarehouseLayer(
                    name="detail",
                    purpose="Store cleaned event-level records.",
                    tables=sorted(layer_tables["detail"]),
                    inputEvents=accepted,
                    outputRows=accepted,
                ),
                WarehouseLayer(
                    name="feature",
                    purpose="Store reusable calculated feature values.",
                    tables=sorted(layer_tables["feature"]),
                    inputEvents=accepted,
                    outputRows=sum(1 for event in events if event.event_type == "feature.updated"),
                ),
                WarehouseLayer(
                    name="analysis",
                    purpose="Store serving tables for ranking, reports, AI, and backtesting.",
                    tables=sorted(layer_tables["analysis"]),
                    inputEvents=accepted,
                    outputRows=len(layer_tables["analysis"]),
                ),
            ]
        )


class LocalDataLake:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path("data_lake")

    def write(self, events: list[PipelineEvent], dataset: str) -> DataLakeManifest:
        dataset = _safe_name(dataset)
        files_by_partition: dict[str, list[str]] = defaultdict(list)
        for event in events:
            partition = (
                f"dataset={dataset}/event_type={_safe_name(event.event_type)}/"
                f"dt={event.timestamp // 86_400_000}"
            )
            path = self.root / partition / "part-00000.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(event.model_dump_json() + "\n")
            files_by_partition[partition].append(str(path))

        files = sorted({path for paths in files_by_partition.values() for path in paths})
        return DataLakeManifest(
            dataset=dataset,
            root=str(self.root),
            files=files,
            rowCount=len(events),
            partitions=sorted(files_by_partition),
        )


class DataFreshnessMonitor:
    def report(
        self,
        events: list[PipelineEvent],
        expected_symbols: list[str],
        max_delay_ms: int,
        expected_interval_ms: int,
    ) -> DataFreshnessReport:
        current = now_ms()
        latest_by_symbol: dict[str, int] = {}
        for event in events:
            symbol = str(event.data.get("symbol", "market")).upper()
            latest_by_symbol[symbol] = max(latest_by_symbol.get(symbol, 0), event.timestamp)

        normalized_expected = {symbol.upper() for symbol in expected_symbols}
        missing = sorted(symbol for symbol in normalized_expected if symbol not in latest_by_symbol)
        delays = [max(0, current - timestamp) for timestamp in latest_by_symbol.values()]
        stale = sum(1 for delay in delays if delay > max_delay_ms)
        event_loss = [
            {
                "symbol": symbol,
                "lastTimestamp": timestamp,
                "delayMs": max(0, current - timestamp),
                "expectedIntervalMs": expected_interval_ms,
            }
            for symbol, timestamp in sorted(latest_by_symbol.items())
            if current - timestamp > expected_interval_ms * 2
        ]
        status = "ok" if not missing and stale == 0 and not event_loss else "degraded"
        return DataFreshnessReport(
            totalEvents=len(events),
            staleEvents=stale,
            missingSymbols=missing,
            maxDelayMs=max(delays, default=0),
            eventLossSuspicions=event_loss,
            status=status,
        )


class GovernanceCatalog:
    def report(self, events: list[PipelineEvent]) -> GovernanceReport:
        nodes: dict[str, LineageNode] = {}
        edges: list[LineageEdge] = []
        owners: dict[str, str] = {}
        classifications: dict[str, str] = {}
        lifecycle: dict[str, str] = {}

        for event in events:
            domain = event.event_type.split(".", 1)[0]
            owner = OWNER_BY_DOMAIN.get(domain, "data-platform")
            table = TABLE_BY_EVENT_TYPE.get(event.event_type, "event_dead_letter")
            source_id = f"source:{event.source}"
            event_id = f"event:{event.event_type}"
            table_id = f"table:{table}"

            nodes[source_id] = LineageNode(id=source_id, type="source", label=event.source)
            nodes[event_id] = LineageNode(id=event_id, type="event", label=event.event_type)
            nodes[table_id] = LineageNode(
                id=table_id,
                type="table",
                label=table,
                metadata={"owner": owner},
            )
            edges.append(LineageEdge(source=source_id, target=event_id, relation="emits"))
            edges.append(LineageEdge(source=event_id, target=table_id, relation="routes_to"))
            owners[table] = owner
            classifications[table] = "sensitive" if domain in {"user", "billing"} else "internal"
            lifecycle[table] = "hot" if domain in {"market", "feature", "ranking"} else "warm"

        return GovernanceReport(
            owners=owners,
            classifications=classifications,
            lifecycle=lifecycle,
            nodes=sorted(nodes.values(), key=lambda node: node.id),
            edges=_dedupe_edges(edges),
        )


def _float_or_zero(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.=-]+", "_", value.strip())[:120] or "unknown"


def _dedupe_edges(edges: list[LineageEdge]) -> list[LineageEdge]:
    seen: set[tuple[str, str, str]] = set()
    output: list[LineageEdge] = []
    for edge in edges:
        key = (edge.source, edge.target, edge.relation)
        if key not in seen:
            seen.add(key)
            output.append(edge)
    return output
