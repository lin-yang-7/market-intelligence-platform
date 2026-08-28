# Market Intelligence Platform 待办清单

## 已完成

- [x] 以 `docs/` 作为实现基线。
- [x] 初始化 Git 仓库。
- [x] 创建仓库骨架：`backend/`、`frontend/`、`ai-engine/`、`data-platform/`、`deployment/`、`scripts/`、`sql/`。
- [x] 添加 Python 项目元数据和依赖文件。
- [x] 添加共享响应、错误处理、请求 ID、配置、模型、鉴权、限流和 Kafka 辅助模块。
- [x] 实现 Market Service MVP。
- [x] 实现 Collector Service MVP，包含 Binance 和 mock connector。
- [x] 实现 API Gateway MVP。
- [x] 实现 Auth Service 健康检查。
- [x] 添加 MySQL 和 ClickHouse 基础 SQL。
- [x] 添加 Docker Compose 文件供后续联调使用，当前开发保持不依赖 Docker。
- [x] 实现纯 Python smoke 检查。
- [x] 实现 Feature Service MVP。
- [x] 实现 Ranking Service MVP。
- [x] 实现 Signal Service MVP。
- [x] 添加 Market -> Feature -> Ranking -> Signal 纯 Python smoke 流程。
- [x] 添加 Signal API 测试。
- [x] 实现 Alert Service MVP。
- [x] 添加 Signal -> Alert 纯 Python smoke 流程。
- [x] 添加 Alert API 测试。
- [x] 实现 Screener Service MVP。
- [x] 添加 Feature -> Screener 纯 Python smoke 流程。
- [x] 添加 Screener API 测试。
- [x] 添加 Kline 和 Trade API。
- [x] 添加 Market Kline/Trade 纯 Python smoke 流程。
- [x] 添加内存版历史 feature 和 signal 存储。
- [x] 添加 Feature/Signal history 纯 Python smoke 流程。
- [x] 在现有接口后补真实 Redis/Kafka 适配器。
- [x] 添加 Redis/Kafka 适配器 fake-client 测试和 smoke 流程。
- [x] 添加 ClickHouse repository 和 market/features/signals 历史数据迁移。
- [x] 添加 ClickHouse fake-client 测试和 smoke 流程。
- [x] 添加前端 Dashboard MVP。
- [x] 成功运行前端 Vue/Vite 构建。
- [x] 添加 Market、Feature、Ranking、Kafka 辅助模块和限流的单元/API 测试。
- [x] 成功运行 pytest。
- [x] 成功运行 ruff。
- [x] 添加 WebSocket Service MVP。
- [x] 前端 Dashboard 接入 WebSocket 状态和实时事件。
- [x] 添加 WebSocket API 测试和 smoke 流程。
- [x] 添加前端主导航和轻量页面切换。
- [x] 添加前端长多资金流页面 MVP。
- [x] 添加前端排行榜页面 MVP。
- [x] 添加前端信号中心页面 MVP。
- [x] 添加前端告警中心页面 MVP。
- [x] 补 AI Engine MVP 骨架。
- [x] API Gateway 接入 AI Engine 预测和解释接口。
- [x] 补 Data Platform MVP 骨架。
- [x] Data Platform 添加事件质量检查、路由计划和处理接口。
- [x] 将 AI Engine 预测结果接入 Signal/Ranking 业务流。
- [x] 将 Data Platform 处理器接入 ClickHouse 写入链路。
- [x] 将 Data Platform 处理器接入 Kafka 消费链路。
- [x] 实现 Notification Service MVP。
- [x] API Gateway 接入 Notification Service。
- [x] 添加 SSE 站内实时推送。
- [x] 添加 WebSocket notification.sent 推送通道。
- [x] 实现 User Service MVP。
- [x] 实现用户注册、登录、profile 和 JWT token。
- [x] 实现 API Key 创建、列表和禁用。
- [x] API Gateway 接入 User Service。
- [x] 实现套餐、订阅和用量 API MVP。
- [x] 添加订阅和用量表 baseline。
- [x] 添加前端账号页面 MVP。
- [x] 添加前端 API Key 管理页面 MVP。
- [x] 添加前端套餐和用量页面 MVP。
- [x] 添加前端登录/注册页面 MVP。
- [x] 添加前端本地登录态和退出流程。
- [x] 前端账号 API 优先接入真实 API Gateway/User Service。
- [x] API Gateway 透传 Authorization 和 X-API-Key 请求头。
- [x] 实现 History Service MVP。
- [x] API Gateway 接入 History Service。
- [x] History Service 聚合 K 线、feature 历史、signal 历史和 timeline。
- [x] 添加前端历史分析页面 MVP。
- [x] 实现独立 Score Service MVP。
- [x] API Gateway 接入 Score Service。
- [x] Ranking Service 优先接入 Score Service，失败时回退本地评分。
- [x] 实现 Rule Service MVP。
- [x] API Gateway 接入 Rule Service。
- [x] Rule Service 支持规则 CRUD 和 payload 条件评估。
- [x] 实现 Feature Store Service MVP。
- [x] API Gateway 接入 Feature Store Service。
- [x] Feature Store 支持 feature catalog、registry、latest、history 和 materialize。
- [x] 添加 Python SDK package MVP。
- [x] SDK 支持 API Key/Bearer 认证、错误转换、重试和主要资源分组。
- [x] 添加 OpenAPI 文档生成脚本。
- [x] 生成各服务 OpenAPI JSON 和 API 索引。
- [x] 添加前端自选列表页面 MVP。
- [x] 添加前端保存筛选器 MVP。
- [x] Ranking 页面添加分页、排序和详情面板 MVP。
- [x] Ranking 页面添加三榜监控视图和上榜、下榜、排名变化事件流。
- [x] Alert Center 添加 SSE/WebSocket 通知偏好配置 MVP。
- [x] 添加模型版本表 baseline。
- [x] 添加通知投递日志表 baseline。
- [x] 添加预测历史、ranking history 和 factor contribution ClickHouse baseline。
- [x] 添加数据库迁移执行器 MVP，支持 plan/apply dry-run 和执行顺序测试。
- [x] 添加计费表 baseline：invoices 和 payment_events。
- [x] 添加备份和数据保留计划 MVP。
- [x] 添加历史图表组件 MVP，展示价格、成交量、评分/feature 趋势和信号标记。
- [x] 添加前端计费页面 MVP，展示 invoices 和 payment events。
- [x] 添加 RBAC 授权 MVP。
- [x] API Gateway 对关键写接口接入权限检查。
- [x] 添加密码和 token 生命周期 MVP。
- [x] JWT 添加 iat/jti，User Service 支持 logout 撤销 token 和改密码。
- [x] 添加 API 签名校验 MVP。
- [x] SDK 支持 HMAC-SHA256 请求签名头。
- [x] 添加审计日志 MVP。
- [x] User Service 记录登录、登出、改密码、API Key 创建和禁用审计事件。
- [x] Ranking Service 添加三榜监控生命周期：上榜、下榜、排名变化。
- [x] 添加 Ranking Monitor 后台 worker，持续扫描异动看涨、机会看涨、风险看跌。
- [x] 添加 ranking.monitor.updated、ranking.entered、ranking.exited、ranking.moved WebSocket 推送事件。
- [x] 添加 ranking monitor event ClickHouse baseline 和 Data Platform 入库映射。
- [x] Feature Service 添加主力净流入、20%-30% 主力比例、支撑位和压力位 MVP。
- [x] 添加主力压力/支撑位解读 API，并接入 API Gateway 和 Ranking 详情页。
- [x] Market Service 添加 Funding、Open Interest、Liquidation API MVP。
- [x] 添加衍生品 ClickHouse baseline 和 Data Platform 入库映射。
- [x] Feature Service 添加资金费率压力、持仓变化、爆仓压力、主动买卖差衍生品因子。
- [x] 主力压力/支撑位解读接入衍生品压力因子。
- [x] Collector Service 添加 Binance Funding、Open Interest、Liquidation 采集和 Kafka 发布。
- [x] Mock Collector 添加衍生品事件，smoke 脚本覆盖衍生品输出。
- [x] Market Worker 消费 Funding、Open Interest、Liquidation 事件并写入 Market Repository。
- [x] Feature Worker 消费 ticker、Funding、Open Interest、Liquidation、Trade 事件并生成特征更新。
- [x] Docker Compose 添加 Feature Worker，并让 Market、Feature、Ranking、Screener 共享 Redis 存储。
- [x] Ranking Item 添加策略状态、信号颜色、命中标签和交易解读字段。
- [x] 三榜评分接入衍生品压力/支撑因子，风险看跌可识别爆仓和主动卖出压力。
- [x] Ranking Monitor 添加跨周期策略事件：首次异动、FOMO、追踪结束、BTC/ETH 趋势切换、批量风险看跌。
- [x] 添加 ranking.strategy WebSocket/SSE 推送和 Data Platform 入库映射。
- [x] 前端 Ranking 页面订阅并展示 ranking.strategy 策略事件、严重级别和说明。
- [x] Data Platform 添加 ranking monitor 历史事件查询 API。
- [x] History Service 和 API Gateway 接入 ranking monitor 历史事件查询。
- [x] 前端 Ranking 页面刷新后加载历史监控/策略事件回放。
- [x] HTTP 服务统一添加 `/ready` readiness 和 `/metrics` Prometheus MVP 指标。
- [x] 添加部署健康检查脚本 `scripts/check_deployment_health.py`。
- [x] 添加生产 Docker 部署 runbook MVP。
- [x] 添加灾备 runbook MVP 和灾备 readiness 校验脚本。
- [x] 添加 GitHub Actions CI MVP：Python lint/test、smoke、灾备校验、前端构建、Docker 镜像构建。
- [x] 添加本地 CI 等价脚本 `scripts/run_ci.py`。
- [x] 添加 JSON 结构化日志、HTTP 请求日志中间件和日志 runbook MVP。
- [x] 添加 Kubernetes manifests MVP、Ingress、readiness/liveness、资源限制和校验脚本。
- [x] 添加 Prometheus scrape 配置、Grafana datasource/dashboard 和监控校验脚本 MVP。
- [x] 添加 GitHub Actions CD MVP：手动触发、GHCR 镜像推送、SSH Docker Compose 部署、健康验证和回滚说明。
- [x] 添加生产 compose 镜像覆盖文件 `deployment/docker-compose.prod.yml`。
- [x] 添加 Docker 集成测试 MVP：本地静态校验、GitHub Actions 启动 auth-service 容器并检查 `/ready`。

## 完整版缺口清单

### 后端服务

- [x] 拆出独立 Score Service MVP。
- [x] 实现 Rule Service MVP。
- [x] 实现 History Service MVP。
- [x] 实现 Feature Store Service MVP。
- [x] 实现 Ranking Monitor Worker MVP。
- [x] 实现三榜上榜、下榜、排名变化事件流 MVP。
- [x] 实现主力压力/支撑位解读 MVP。
- [x] 实现 Funding/Open Interest/Liquidation Market API MVP。
- [x] 实现衍生品 Collector MVP。
- [x] 实现衍生品 Market/Feature 实时 worker 链路 MVP。
- [x] 实现三榜策略解释字段 MVP。
- [x] 实现三榜跨周期策略事件 MVP。

### API

- [x] 实现用户和 API Key API MVP。
- [x] 实现套餐、用量相关 API MVP。
- [x] 实现 Notification API MVP。
- [x] 实现 Rule API MVP。
- [x] 实现 Feature Store API MVP。
- [x] 实现 Ranking Monitor API MVP。
- [x] 实现主力压力/支撑位解读 API MVP。
- [x] 实现衍生品 Market API MVP。
- [x] 生成 API 文档。
- [x] 实现 Python SDK package MVP。

### 前端

- [x] 账号页面 MVP。
- [x] API Key 管理页面 MVP。
- [x] 套餐和用量页面 MVP。
- [x] 登录和注册页面 MVP。
- [x] 本地登录态和退出流程。
- [x] 真实后端登录态接入 MVP。
- [x] 计费页面 MVP。
- [ ] 支付集成。
- [x] 告警通道配置页面 MVP，仅支持 SSE/WebSocket。
- [x] 历史分析页面 MVP。
- [x] K线、成交量、评分、信号趋势图表 MVP。
- [x] 保存筛选器和自选列表 MVP。
- [x] 分页、排序、详情抽屉 MVP。
- [x] 三榜监控当前在榜、BTC/ETH 状态、风险批量提示和事件流 MVP。
- [x] Ranking 详情页展示主力支撑位、压力位、净流入和解读 MVP。
- [x] Ranking 事件流展示策略事件、严重级别和解释正文 MVP。
- [x] Ranking 事件流支持历史监控/策略事件回放 MVP。

### AI Engine

- [ ] 训练 pipeline。
- [ ] 模型注册、版本切换和回滚。
- [ ] A/B 测试。
- [ ] 回测和模型评估。
- [ ] 模型监控。
- [ ] 深度 Explainable AI 报告。
- [ ] LLM Assistant。

### Data Platform

- [x] Ranking monitor event routing and ClickHouse write mapping。
- [x] Funding/Open Interest/Liquidation event routing and ClickHouse write mapping。
- [x] Funding/Open Interest/Liquidation event to Feature Worker processing MVP。
- [x] Ranking monitor strategy event history query MVP。
- [x] Flink 或实时流处理任务 MVP：内置 stream job API，后续可替换 Flink 执行引擎。
- [x] 批处理 pipeline MVP。
- [x] 数据仓库分层 MVP。
- [x] 数据湖 MVP：本地分区 JSONL 写入。
- [x] 数据质量报告 API MVP。
- [x] 数据延迟和事件丢失监控 MVP。
- [x] 数据血缘和治理 MVP。

### 数据库

- [x] 用户和 API Key 表 baseline。
- [x] 订阅和额度表 baseline。
- [x] 计费表 baseline。
- [x] 通知投递和推送日志表 baseline。
- [x] 模型版本和预测历史表 baseline。
- [x] Ranking history 和 factor contribution 表 baseline。
- [x] Ranking monitor event 表 baseline。
- [x] Funding/Open Interest/Liquidation 表 baseline。
- [x] 迁移执行器 MVP。
- [x] 备份和保留任务 MVP。

### 告警和推送

- [x] 将 Alert Service 替换为站内实时通知触发流。
- [x] 投递重试和死信。
- [x] 推送去重。
- [x] 推送历史和状态跟踪。
- [x] 用户级通知偏好。
- [x] 三榜监控事件 WebSocket/SSE 推送。

### 安全

- [x] 用户注册、登录和 JWT 认证 MVP。
- [x] RBAC 授权 MVP。
- [x] 密码和 token 生命周期 MVP。
- [x] API 签名校验 MVP。
- [x] 审计日志 MVP。
- [x] 敏感配置加密 MVP。
- [x] 安全测试 MVP。

### DevOps

- [x] Docker 集成测试 MVP。
- [x] Kubernetes manifests MVP。
- [x] CI pipeline MVP。
- [x] CD pipeline MVP。
- [x] Prometheus metrics MVP。
- [x] Grafana dashboards MVP。
- [x] 集中式日志 MVP：结构化 stdout 和请求日志，待接 Loki/ELK。
- [x] Health check 和 readiness 策略 MVP。
- [x] 生产部署 runbook MVP。
- [x] 灾备 runbook MVP。

### 产品运营

- [x] SaaS 套餐管理 MVP。
- [x] 用量计量 MVP。
- [ ] 计费集成。
- [x] 管理后台 MVP：基于 GitHub `vbenjs/vben-admin-thin-next` 的后台布局和权限路由思路改造。
- [ ] 用户行为分析。
- [ ] 产品运营看板。
- [ ] 增长和留存流程。
