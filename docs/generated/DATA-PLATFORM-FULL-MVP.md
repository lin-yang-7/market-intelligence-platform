# Data Platform Full MVP

## Scope

This implementation adds production-facing Data Platform capabilities without
requiring external Flink, S3, or a separate governance product during local
development. The APIs define the stable contract; the execution engine can later
be replaced by Flink, object storage, and a managed data catalog.

## Implemented Capabilities

- Stream processing job: `POST /v1/data/stream/process`
- Batch pipeline job: `POST /v1/data/batch/run`
- Data warehouse layer plan: `POST /v1/data/warehouse/plan`
- Data lake partitioned JSONL writer: `POST /v1/data/lake/write`
- Data freshness, delay, and event-loss report: `POST /v1/data/freshness/report`
- Data governance ownership and lineage graph: `POST /v1/data/governance/lineage`

## Completion Check

```powershell
python scripts\validate_data_platform_full.py
```

The check verifies required source files, generated OpenAPI endpoints, checklist
markers, and runtime-data ignore rules. It also runs in `scripts/run_ci.py`.

## Warehouse Layers

- Raw: source events for replay and audit.
- Detail: cleaned event-level records.
- Feature: reusable feature values.
- Analysis: serving data for ranking, reports, AI, and backtesting.

## Data Lake Layout

Local MVP writes JSONL files under `data_lake/`:

```text
data_lake/
  dataset=raw_events/
    event_type=market.ticker/
      dt=<epoch-day>/
        part-00000.jsonl
```

`data_lake/` is ignored by Git because it is runtime data.

## Monitoring

The freshness report checks:

- Missing expected symbols.
- Events delayed beyond `maxDelayMs`.
- Event-loss suspicion when latest symbol data exceeds `expectedIntervalMs * 2`.

## Governance

The governance report includes:

- Table owner mapping.
- Table classification.
- Hot/warm lifecycle stage.
- Source -> event -> table lineage edges.

## Current Boundary

This is a local execution MVP. It does not yet run a real Flink cluster, object
storage, or external data catalog, but it preserves API contracts and testable
business behavior for those later replacements.
