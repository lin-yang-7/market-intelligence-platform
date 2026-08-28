# 内部简化版智能选币程序

单文件程序：`scripts/internal_smart_coin_app.py`

## 启动

```powershell
python scripts\internal_smart_coin_app.py --host 127.0.0.1 --port 8765 --interval 60 --limit 8
```

默认扫描全部 Binance USDT 现货。

指定币种仅用于调试：

```powershell
python scripts\internal_smart_coin_app.py BTCUSDT ETHUSDT SOLUSDT
```

## 访问

- 网页看板：`http://127.0.0.1:8765/`
- REST 快照：`http://127.0.0.1:8765/api/snapshot`
- SSE 推送：`http://127.0.0.1:8765/stream`
- WebSocket 推送：`ws://127.0.0.1:8765/ws`

## 三个列表

- 异动看涨：在全币种中按 24h 涨幅、振幅、成交额和成交活跃度排序。
- 机会看涨：在全币种中按正向动量、成交额和成交活跃度排序，降低过高振幅权重。
- 风险看跌：在全币种中按下跌幅度、振幅和流动性不足排序。

三个列表各自独立排序，同一个币种可以同时出现在多个列表里。

## 分数

所有分数都是 0-100 百分制。

```text
positive_score = min(100, max(0, 24h涨幅) * 10)
negative_score = min(100, max(0, -24h涨幅) * 10)
amplitude_score = min(100, 24h振幅 * 8)
volume_score = min(100, quoteVolume / 20,000,000)
trade_score = min(100, tradeCount / 20,000)
```

```text
异动看涨 =
positive_score * 0.45
+ amplitude_score * 0.25
+ volume_score * 0.20
+ trade_score * 0.10
```

```text
机会看涨 =
positive_score * 0.40
+ volume_score * 0.35
+ trade_score * 0.20
+ stability_score * 0.05
```

```text
风险看跌 =
negative_score * 0.55
+ amplitude_score * 0.25
+ liquidity_risk * 0.20
```
