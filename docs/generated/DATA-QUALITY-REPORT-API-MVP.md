# Data Quality Report API MVP

## Scope

Data Platform exposes a batch quality report endpoint:

```text
POST /v1/data/quality/report
```

The endpoint accepts up to 1000 `PipelineEvent` objects and returns:

- Total, accepted, and rejected event counts.
- Warning and error event counts.
- Average missing-field rate.
- Average and maximum event delay.
- Per-event-type buckets with the same metrics.

## Request

```json
{
  "events": [
    {
      "event_type": "market.ticker",
      "timestamp": 1700000000000,
      "source": "binance",
      "data": {
        "symbol": "BTCUSDT",
        "price": 68000
      }
    }
  ]
}
```

## Response

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "totalEvents": 1,
    "acceptedEvents": 1,
    "rejectedEvents": 0,
    "warningEvents": 0,
    "errorEvents": 0,
    "avgMissingRate": 0,
    "avgDelayMs": 10,
    "maxDelayMs": 10,
    "buckets": []
  }
}
```

## Validation Rules

The report reuses the same quality checker as `/v1/data/validate`.
Current MVP rules cover:

- Required fields per event type.
- Positive price validation.
- Future timestamp rejection.
- Five-minute delay warning.

## Remaining Work

- Persist rolling quality windows.
- Add source-level SLA thresholds.
- Add event loss and delay monitoring dashboards.
- Add data lineage joins to the quality report.
