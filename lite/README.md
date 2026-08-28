# Market Intelligence Lite

Lite 版只移除了账号、计费、运营后台、对外 SDK/API 与监控界面；它并未移除
核心数据链路。Collector、Kafka、质量校验、Market、Feature、Score、Ranking、
Signal、Rule、Alert、Notification、WebSocket、历史存储仍运行在 Docker 内网。

宿主机只开放前端端口（默认 `18080`）。网关和 WebSocket 没有主机端口；前端通过
同域反向代理访问仅用于页面展示的读取请求，不能作为独立对外 API 使用。

## 环境与部署

服务器建议使用 Ubuntu 22.04/24.04、Docker Engine 及 Docker Compose v2。将完整仓库
上传或克隆到服务器后，进入 `lite/` 目录创建环境文件并设置强随机内部令牌：

```bash
cd /opt/market-intelligence-platform/lite
cp .env.example .env
secret=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
sed -i "s|^INTERNAL_SERVICE_TOKEN=.*|INTERNAL_SERVICE_TOKEN=$secret|" .env
```

启动：

```powershell
docker compose --env-file .env up -d --build
```

首次采集后需要等待约 1--2 分钟，Market Worker 和 Feature Worker 才能产生排行。
访问 `http://SERVER_IP/` 查看预测和排行。行情、特征、评分、排行、信号都保存在
ClickHouse；Redis 只保存实时查询状态。

常用环境变量：

| 变量 | 默认值 | 作用 |
| --- | ---: | --- |
| `INTERNAL_SERVICE_TOKEN` | 必填 | 容器间内部调用令牌，必须替换示例值 |
| `LITE_BIND_ADDRESS` | `127.0.0.1` | Lite 监听地址；域名部署时保持本机监听 |
| `LITE_FRONTEND_PORT` | `18080` | Nginx 转发到的本机端口 |
| `COLLECTOR_AUTO_TOP_SYMBOLS` | `50` | 实时采集的成交额前 N 个 USDT 标的 |
| `COLLECTOR_DERIVATIVES_TOP_SYMBOLS` | `20` | 衍生品采集覆盖数量 |
| `HISTORICAL_BACKFILL_ENABLED` | `true` | 是否每天补充缺失 K 线 |
| `SIGNAL_GENERATOR_INTERVAL_SECONDS` | `60` | 排行转信号的内部周期 |

启动后检查：

```bash
docker compose ps
docker compose logs -f collector-service feature-worker signal-generator-worker
```

## 域名与 HTTPS

先在 DNS 中为域名（例如 `lite.example.com`）添加指向服务器公网 IP 的 A 记录。然后：

```bash
sudo cp nginx/market-intelligence-lite.conf /etc/nginx/conf.d/market-intelligence-lite.conf
sudo sed -i 's/lite\.example\.com/你的实际域名/g' /etc/nginx/conf.d/market-intelligence-lite.conf
sudo nginx -t && sudo systemctl reload nginx
```

Lite 默认仅监听 `127.0.0.1:18080`，不需要开放 `18080`。安全组/防火墙仅开放 TCP
`80`、`443` 和管理用 `22`。使用 Certbot 签发证书：

```bash
sudo certbot --nginx -d 你的实际域名
```

完成后访问 `https://你的实际域名/`。不要让 Lite 容器直接绑定 `80` 或 `443`。

## 不对外开放的组件

`api-gateway`、`websocket-service`、Redis、Kafka、ClickHouse 和所有业务服务均
不配置 `ports`，只能被同一个 Compose 网络中的容器调用。请在防火墙中只开放
`18080`（以及管理所需的 `22`）。
