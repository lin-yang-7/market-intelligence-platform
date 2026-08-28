# Implementation Gap Checklist

Version: 0.1

This checklist tracks the gap between the current MVP implementation and the
complete platform described under `docs/`.

## 1. Backend Services

- [x] Market Service MVP
- [x] Collector Service MVP
- [x] Feature Service MVP
- [x] Ranking Service MVP
- [x] Signal Service MVP
- [x] Screener Service MVP
- [x] Alert Service MVP
- [x] API Gateway MVP
- [x] WebSocket Service MVP
- [x] AI Engine MVP
- [x] Data Platform MVP
- [x] User Service MVP
- [x] Notification Service MVP
- [x] History Service MVP
- [x] Independent Score Service MVP
- [x] Rule Service MVP
- [x] Feature Store Service MVP
- [x] Ranking Monitor Worker MVP
- [x] Ranking entered/exited/moved lifecycle MVP
- [x] Main-force pressure/support interpretation MVP
- [x] Funding/Open Interest/Liquidation Market Service MVP
- [x] Funding/Open Interest/Liquidation Collector MVP
- [x] Funding/Open Interest/Liquidation Market and Feature Worker MVP
- [x] Ranking item strategy state, signal color, reason tags, and guidance MVP
- [x] Ranking monitor strategy events for first abnormal, FOMO, tracking ended, BTC/ETH trend changes, and batch bearish risk MVP

## 2. API

- [x] Market API
- [x] Feature API
- [x] Ranking API
- [x] Screener API
- [x] Signal API
- [x] Alert API
- [x] WebSocket API MVP
- [x] Unified response format
- [x] Notification API MVP
- [x] User API MVP
- [x] API Key management API MVP
- [x] Subscription and usage API MVP
- [x] History API MVP
- [x] Score API MVP
- [x] Rule API MVP
- [x] Feature Store API MVP
- [x] Ranking Monitor API MVP
- [x] Main-force pressure/support API MVP
- [x] Funding/Open Interest/Liquidation Market API MVP
- [x] Python SDK package MVP
- [x] API documentation generation

## 3. Frontend

- [x] Dashboard MVP
- [x] Long Inflow page MVP
- [x] Ranking page MVP
- [x] Signal page MVP
- [x] Alert Center page MVP
- [x] Account page MVP
- [x] API Key management page MVP
- [x] Subscription and usage page MVP
- [x] Login and register page MVP
- [x] Local auth state and sign-out flow
- [x] Real backend auth state wiring MVP
- [x] Historical analysis page MVP
- [x] Billing page MVP
- [ ] Payment integration
- [x] Alert channel configuration page MVP for SSE/WebSocket
- [x] Real chart components for Kline, volume, score, and signal trend MVP
- [x] Saved filters and watchlists MVP
- [x] Pagination, sorting, and detail drawers MVP
- [x] Ranking monitor current list and event feed MVP
- [x] Ranking detail pressure/support interpretation MVP
- [x] Ranking strategy event feed with severity and explanation MVP
- [x] Ranking monitor historical event replay MVP

## 4. AI Engine

- [x] Deterministic hybrid scoring MVP
- [x] Prediction API
- [x] Explanation API
- [x] Ranking and Signal integration
- [ ] Training pipeline
- [ ] Model registry and version switching
- [ ] Model rollback
- [ ] A/B testing
- [ ] Backtesting and model evaluation
- [ ] Model monitoring
- [ ] Explainable AI detail report
- [ ] LLM assistant

## 5. Data Platform

- [x] Pipeline event schema
- [x] Data quality checks
- [x] Event routing
- [x] ClickHouse write mapping
- [x] Kafka consumer worker
- [x] Ranking monitor event routing and ClickHouse write mapping
- [x] Funding/Open Interest/Liquidation event routing and ClickHouse write mapping
- [x] Funding/Open Interest/Liquidation event to Feature Worker processing MVP
- [x] Ranking monitor strategy event history query MVP
- [x] Flink or stream processing jobs MVP
- [x] Batch pipeline MVP
- [x] Data warehouse layers MVP
- [x] Data lake MVP
- [x] Data quality report API MVP
- [x] Data delay and event loss monitoring MVP
- [x] Data lineage and governance MVP

## 6. Database

- [x] MySQL baseline schema
- [x] ClickHouse baseline schema
- [x] Redis helpers
- [x] ClickHouse history repositories
- [x] User tables baseline
- [x] API key tables baseline
- [x] Subscription tables baseline
- [x] Usage and quota tables baseline
- [x] Billing tables baseline
- [x] Notification and delivery log tables baseline
- [x] Model version and prediction history tables baseline
- [x] Ranking history and factor contribution tables baseline
- [x] Ranking monitor event table baseline
- [x] Funding/Open Interest/Liquidation tables baseline
- [x] Migration runner MVP
- [x] Backup and retention jobs MVP

## 7. Alerting And Notification

- [x] Alert Service MVP
- [x] Alert rule API MVP
- [x] Console delivery
- [x] SSE realtime push
- [x] WebSocket realtime push
- [x] Alert Service replacement with realtime notification flow
- [x] Delivery retry and dead letter handling
- [x] Push deduplication
- [x] Push history and status tracking
- [x] Per-user notification preferences
- [x] Ranking monitor WebSocket/SSE push events
- [x] Ranking strategy WebSocket/SSE push events and Data Platform routing

## 8. Security

- [x] Basic API key parsing
- [x] Basic rate limiting
- [x] User authentication MVP
- [x] RBAC authorization MVP
- [x] Password and token lifecycle MVP
- [x] API signature verification MVP
- [x] Audit logs MVP
- [x] Sensitive configuration encryption MVP
- [x] Security tests MVP

## 9. DevOps

- [x] Docker Compose file
- [x] Docker integration test MVP
- [x] Kubernetes manifests MVP
- [x] CI pipeline MVP
- [x] CD pipeline MVP
- [x] Prometheus-format MVP metrics endpoint
- [x] Grafana dashboards MVP
- [x] Centralized logging MVP with structured stdout request logs
- [x] Health check and readiness policy MVP
- [x] Production deployment runbook MVP
- [x] Disaster recovery runbook MVP

## 10. Product Operation

- [x] SaaS plan management MVP
- [x] Usage metering MVP
- [ ] Billing integration
- [x] Admin console MVP
- [ ] User behavior analytics
- [ ] Product operation dashboard
- [ ] Growth and retention workflows

## Recommended Build Order

1. Notification Service and real push channels.
2. User Service, API keys, quota, and auth hardening.
3. Independent Score Service and richer multi-timeframe signals.
4. Frontend account, API key, alert settings, and historical analysis pages.
5. AI training, backtesting, and model registry.
6. DevOps, monitoring, Docker integration, and production deployment.
