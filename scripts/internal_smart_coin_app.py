# ruff: noqa: E501
import argparse
import asyncio
import json
import time
from dataclasses import asdict, dataclass
from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse

DEFAULT_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "LINKUSDT",
    "AVAXUSDT",
    "TRXUSDT",
    "TONUSDT",
    "SUIUSDT",
]


@dataclass(frozen=True)
class CoinRow:
    symbol: str
    price: float
    change24h: float
    quoteVolume: float
    tradeCount: int
    abnormalBullishScore: float
    opportunityBullishScore: float
    riskBearishScore: float
    reason: str


@dataclass(frozen=True)
class CoinSnapshot:
    updatedAt: int
    source: str
    abnormalBullish: list[CoinRow]
    opportunityBullish: list[CoinRow]
    riskBearish: list[CoinRow]
    changes: dict[str, Any]


class SnapshotStore:
    def __init__(self) -> None:
        self.snapshot = CoinSnapshot(
            updatedAt=0,
            source="binance",
            abnormalBullish=[],
            opportunityBullish=[],
            riskBearish=[],
            changes={},
        )
        self.subscribers: set[asyncio.Queue[str]] = set()

    def current(self) -> dict[str, Any]:
        return snapshot_to_dict(self.snapshot)

    async def publish(self, snapshot: CoinSnapshot) -> None:
        snapshot = with_changes(self.snapshot, snapshot)
        self.snapshot = snapshot
        message = json.dumps(snapshot_to_dict(snapshot), ensure_ascii=False)
        stale: list[asyncio.Queue[str]] = []
        for queue in self.subscribers:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                stale.append(queue)
        for queue in stale:
            self.subscribers.discard(queue)

    def subscribe(self) -> asyncio.Queue[str]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=3)
        self.subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[str]) -> None:
        self.subscribers.discard(queue)


async def fetch_binance_tickers(symbols: list[str] | None = None) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(base_url="https://api.binance.com", timeout=15) as client:
        response = await client.get("/api/v3/ticker/24hr")
        response.raise_for_status()
        rows = response.json()
    wanted = {symbol.upper() for symbol in symbols} if symbols else None
    return [
        row
        for row in rows
        if row.get("symbol", "").endswith("USDT")
        and (wanted is None or row.get("symbol") in wanted)
        and not row.get("symbol", "").endswith(("UPUSDT", "DOWNUSDT", "BULLUSDT", "BEARUSDT"))
    ]


def score_ticker(row: dict[str, Any]) -> CoinRow:
    symbol = str(row["symbol"]).upper()
    price = float(row["lastPrice"])
    change = float(row["priceChangePercent"])
    quote_volume = float(row["quoteVolume"])
    trade_count = int(row.get("count") or 0)
    high = float(row["highPrice"])
    low = float(row["lowPrice"])
    open_price = float(row["openPrice"])
    amplitude = ((high - low) / max(open_price, 1e-9)) * 100
    volume_score = min(100.0, quote_volume / 20_000_000)
    trade_score = min(100.0, trade_count / 20_000)
    positive = max(0.0, change)
    negative = max(0.0, -change)
    positive_score = min(100.0, positive * 10)
    negative_score = min(100.0, negative * 10)
    amplitude_score = min(100.0, amplitude * 8)
    stability_score = max(0.0, 100.0 - amplitude_score)
    liquidity_risk = max(0.0, 100.0 - volume_score)

    abnormal = (
        positive_score * 0.45
        + amplitude_score * 0.25
        + volume_score * 0.20
        + trade_score * 0.10
    )
    opportunity = (
        positive_score * 0.40
        + volume_score * 0.35
        + trade_score * 0.20
        + stability_score * 0.05
    )
    risk = negative_score * 0.55 + amplitude_score * 0.25 + liquidity_risk * 0.20
    reason = reason_for_scores(change, amplitude, volume_score, trade_score)
    return CoinRow(
        symbol=symbol,
        price=round(price, 8),
        change24h=round(change, 4),
        quoteVolume=round(quote_volume, 2),
        tradeCount=trade_count,
        abnormalBullishScore=round(max(0.0, abnormal), 2),
        opportunityBullishScore=round(max(0.0, opportunity), 2),
        riskBearishScore=round(max(0.0, risk), 2),
        reason=reason,
    )


def reason_for_scores(
    change: float,
    amplitude: float,
    volume_score: float,
    trade_score: float,
) -> str:
    reasons = []
    if change >= 5:
        reasons.append("24h momentum")
    if amplitude >= 8:
        reasons.append("wide range")
    if volume_score >= 60:
        reasons.append("high quote volume")
    if trade_score >= 60:
        reasons.append("active trading")
    if change <= -5:
        reasons.append("downside pressure")
    return ", ".join(reasons) or "normal market activity"


def is_abnormal_bullish(row: CoinRow) -> bool:
    return row.abnormalBullishScore >= 35 and row.change24h >= 3 and row.quoteVolume >= 5_000_000


def is_opportunity_bullish(row: CoinRow) -> bool:
    return row.opportunityBullishScore >= 35 and row.change24h >= 1 and row.quoteVolume >= 10_000_000


def is_risk_bearish(row: CoinRow) -> bool:
    return row.riskBearishScore >= 45 and row.change24h <= -3


def build_snapshot(rows: list[CoinRow], limit: int = 8) -> CoinSnapshot:
    abnormal = sorted(
        [row for row in rows if is_abnormal_bullish(row)],
        key=lambda item: item.abnormalBullishScore,
        reverse=True,
    )[:limit]
    opportunity = sorted(
        [row for row in rows if is_opportunity_bullish(row)],
        key=lambda item: item.opportunityBullishScore,
        reverse=True,
    )[:limit]
    risk = sorted(
        [row for row in rows if is_risk_bearish(row)],
        key=lambda item: item.riskBearishScore,
        reverse=True,
    )[:limit]
    return CoinSnapshot(
        updatedAt=int(time.time() * 1000),
        source="binance",
        abnormalBullish=abnormal,
        opportunityBullish=opportunity,
        riskBearish=risk,
        changes={},
    )


def row_score(row: CoinRow, list_name: str) -> float:
    if list_name == "abnormalBullish":
        return row.abnormalBullishScore
    if list_name == "opportunityBullish":
        return row.opportunityBullishScore
    return row.riskBearishScore


def list_changes(previous_rows: list[CoinRow], current_rows: list[CoinRow], list_name: str) -> dict[str, list[dict[str, Any]]]:
    previous = {row.symbol: (index + 1, row) for index, row in enumerate(previous_rows)}
    current = {row.symbol: (index + 1, row) for index, row in enumerate(current_rows)}

    entered = [
        {"symbol": symbol, "toRank": rank, "row": asdict(row)}
        for symbol, (rank, row) in current.items()
        if symbol not in previous
    ]
    exited = [
        {"symbol": symbol, "fromRank": rank, "row": asdict(row)}
        for symbol, (rank, row) in previous.items()
        if symbol not in current
    ]
    moved = []
    for symbol, (rank, row) in current.items():
        if symbol not in previous:
            continue
        previous_rank, previous_row = previous[symbol]
        if previous_rank != rank:
            moved.append(
                {
                    "symbol": symbol,
                    "fromRank": previous_rank,
                    "toRank": rank,
                    "scoreChange": round(row_score(row, list_name) - row_score(previous_row, list_name), 2),
                    "row": asdict(row),
                }
            )
    return {"entered": entered, "exited": exited, "moved": moved}


def with_changes(previous: CoinSnapshot, current: CoinSnapshot) -> CoinSnapshot:
    changes = {
        "abnormalBullish": list_changes(previous.abnormalBullish, current.abnormalBullish, "abnormalBullish"),
        "opportunityBullish": list_changes(previous.opportunityBullish, current.opportunityBullish, "opportunityBullish"),
        "riskBearish": list_changes(previous.riskBearish, current.riskBearish, "riskBearish"),
    }
    return CoinSnapshot(
        updatedAt=current.updatedAt,
        source=current.source,
        abnormalBullish=current.abnormalBullish,
        opportunityBullish=current.opportunityBullish,
        riskBearish=current.riskBearish,
        changes=changes,
    )


def snapshot_to_dict(snapshot: CoinSnapshot) -> dict[str, Any]:
    return {
        "updatedAt": snapshot.updatedAt,
        "source": snapshot.source,
        "abnormalBullish": [asdict(row) for row in snapshot.abnormalBullish],
        "opportunityBullish": [asdict(row) for row in snapshot.opportunityBullish],
        "riskBearish": [asdict(row) for row in snapshot.riskBearish],
        "changes": snapshot.changes,
    }


def create_app(symbols: list[str] | None = None, interval: int = 60, limit: int = 8) -> FastAPI:
    app = FastAPI(title="Internal Smart Coin App", version="0.1.0")
    store = SnapshotStore()
    task: asyncio.Task | None = None

    async def refresh_loop() -> None:
        while True:
            try:
                tickers = await fetch_binance_tickers(symbols)
                scored = [score_ticker(row) for row in tickers]
                await store.publish(build_snapshot(scored, limit=limit))
            except Exception as exc:
                print(f"refresh failed: {exc}")
            await asyncio.sleep(interval)

    @app.on_event("startup")
    async def startup() -> None:
        nonlocal task
        task = asyncio.create_task(refresh_loop())

    @app.on_event("shutdown")
    async def shutdown() -> None:
        if task:
            task.cancel()

    @app.get("/", response_class=HTMLResponse)
    async def home() -> str:
        return HTML_PAGE

    @app.get("/api/snapshot")
    async def snapshot() -> dict[str, Any]:
        return store.current()

    @app.get("/stream")
    async def stream():
        queue = store.subscribe()

        async def events():
            try:
                yield f"data: {json.dumps(store.current(), ensure_ascii=False)}\n\n"
                while True:
                    message = await queue.get()
                    yield f"data: {message}\n\n"
            finally:
                store.unsubscribe(queue)

        return StreamingResponse(events(), media_type="text/event-stream")

    @app.websocket("/ws")
    async def websocket(websocket: WebSocket) -> None:
        await websocket.accept()
        queue = store.subscribe()
        await websocket.send_json(store.current())
        try:
            while True:
                message = await queue.get()
                await websocket.send_text(message)
        except WebSocketDisconnect:
            store.unsubscribe(queue)

    return app


HTML_PAGE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>内部智能选币</title>
  <style>
    body{margin:0;background:#f4f7f5;color:#16211f;font-family:Inter,Arial,sans-serif}
    header{height:56px;background:#fff;border-bottom:1px solid #d9e1dd;display:flex;align-items:center;justify-content:space-between;padding:0 18px}
    main{padding:18px;display:grid;gap:14px;grid-template-columns:repeat(3,minmax(0,1fr))}
    .feed{margin:0 18px 18px;background:#fff;border:1px solid #d9e1dd;border-radius:8px;padding:14px}
    section{background:#fff;border:1px solid #d9e1dd;border-radius:8px;padding:14px;min-width:0}
    h2{font-size:16px;margin:0 0 12px}
    h3{font-size:14px;margin:0 0 10px}
    table{border-collapse:collapse;width:100%;font-size:13px}
    th,td{border-bottom:1px solid #edf1ef;padding:8px;text-align:left;white-space:nowrap}
    th{color:#66736f;font-size:12px}
    .pos{color:#13795b;font-weight:700}.neg{color:#b42318;font-weight:700}
    .event{display:inline-flex;gap:6px;align-items:center;border:1px solid #edf1ef;border-radius:6px;padding:5px 8px;margin:0 6px 6px 0;font-size:12px}
    .enter{border-color:#b7e4cf;background:#f0fff8}.exit{border-color:#f7c6c2;background:#fff5f3}.move{border-color:#c7d7fe;background:#f6f8ff}
    small{color:#66736f}
    @media(max-width:980px){main{grid-template-columns:1fr}}
  </style>
</head>
<body>
  <header><strong>内部智能选币</strong><small id="meta">waiting</small></header>
  <main>
    <section><h2>异动看涨</h2><table id="abnormalBullish"></table></section>
    <section><h2>机会看涨</h2><table id="opportunityBullish"></table></section>
    <section><h2>风险看跌</h2><table id="riskBearish"></table></section>
  </main>
  <div class="feed">
    <h3>榜单变动</h3>
    <div id="changeFeed"><small>waiting</small></div>
  </div>
  <script>
    const fields = {
      abnormalBullish: 'abnormalBullishScore',
      opportunityBullish: 'opportunityBullishScore',
      riskBearish: 'riskBearishScore'
    };
    const labels = {
      abnormalBullish: '异动看涨',
      opportunityBullish: '机会看涨',
      riskBearish: '风险看跌'
    };
    let lastUpdatedAt = 0;
    function renderTable(id, rows) {
      const score = fields[id];
      document.getElementById(id).innerHTML = '<tr><th>#</th><th>币种</th><th>价格</th><th>24h</th><th>分</th></tr>' +
        rows.map((row, i) => `<tr><td>${i+1}</td><td><strong>${row.symbol}</strong><br><small>${row.reason}</small></td><td>${row.price}</td><td class="${row.change24h >= 0 ? 'pos' : 'neg'}">${row.change24h}%</td><td>${row[score].toFixed(1)}</td></tr>`).join('');
    }
    function renderChanges(changes) {
      const items = [];
      Object.entries(changes || {}).forEach(([list, change]) => {
        (change.entered || []).forEach(item => items.push(`<span class="event enter">${labels[list]} 上榜 ${item.symbol} #${item.toRank}</span>`));
        (change.exited || []).forEach(item => items.push(`<span class="event exit">${labels[list]} 下榜 ${item.symbol} #${item.fromRank}</span>`));
        (change.moved || []).forEach(item => items.push(`<span class="event move">${labels[list]} 排名 ${item.symbol} ${item.fromRank}→${item.toRank}</span>`));
      });
      document.getElementById('changeFeed').innerHTML = items.join('') || '<small>本轮无上榜/下榜变化</small>';
    }
    function render(data) {
      if (!data.updatedAt || data.updatedAt < lastUpdatedAt) return;
      lastUpdatedAt = data.updatedAt;
      document.getElementById('meta').textContent = `${data.source} / ${new Date(data.updatedAt).toLocaleTimeString()}`;
      renderTable('abnormalBullish', data.abnormalBullish || []);
      renderTable('opportunityBullish', data.opportunityBullish || []);
      renderTable('riskBearish', data.riskBearish || []);
      renderChanges(data.changes || {});
    }
    function refreshSnapshot() {
      fetch('/api/snapshot', {cache: 'no-store'}).then(r => r.json()).then(render);
    }
    refreshSnapshot();
    setInterval(refreshSnapshot, 15000);
    const events = new EventSource('/stream');
    events.onmessage = event => render(JSON.parse(event.data));
    events.onerror = () => {
      document.getElementById('meta').textContent = `SSE reconnecting / ${new Date().toLocaleTimeString()}`;
    };
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Internal smart coin app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument(
        "symbols",
        nargs="*",
        help="Optional debug symbols. Empty means scan all Binance USDT spot pairs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    symbols = [item.upper() for item in args.symbols] or None
    app = create_app(symbols=symbols, interval=max(10, args.interval), limit=max(1, args.limit))
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
