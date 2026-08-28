# Backup And Retention Plan

## Backup Targets

- mysql:users
- mysql:api_keys
- mysql:subscriptions
- mysql:usage_counters
- mysql:invoices
- mysql:payment_events
- clickhouse:market_ticker
- clickhouse:market_kline
- clickhouse:feature_history
- clickhouse:signal_history
- clickhouse:prediction_history
- clickhouse:ranking_history

## Retention Policies

- market_ticker: hot=30d, cold=365d, delete_after=1095d
- market_kline: hot=90d, cold=730d, delete_after=1825d
- feature_history: hot=90d, cold=730d, delete_after=1825d
- signal_history: hot=180d, cold=1095d, delete_after=2555d
- prediction_history: hot=180d, cold=1095d, delete_after=2555d
- notification_deliveries: hot=30d, cold=365d, delete_after=730d

## Execution Notes

- This MVP plan is declarative and does not delete data.
- Production execution should use database-native backup tooling.
- Destructive retention jobs must run with audited dry-run output first.
