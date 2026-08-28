from mip_common.events import MarketEvent, MarketTickerData
from mip_common.models import model_to_dict
from mip_common.responses import now_ms


class BinanceTickerConnector:
    base_url = "https://api.binance.com"
    futures_base_url = "https://fapi.binance.com"

    async def fetch_top_usdt_symbols(self, limit: int) -> list[str]:
        import httpx

        async with httpx.AsyncClient(base_url=self.base_url, timeout=10) as client:
            response = await client.get("/api/v3/ticker/24hr")
            response.raise_for_status()
            payload = response.json()
        rows = [
            row
            for row in payload
            if str(row.get("symbol", "")).endswith("USDT")
            and float(row.get("quoteVolume") or 0) > 0
        ]
        rows.sort(key=lambda row: float(row.get("quoteVolume") or 0), reverse=True)
        return [str(row["symbol"]) for row in rows[:limit]]

    async def fetch_ticker(self, symbol: str) -> MarketEvent:
        import httpx

        async with httpx.AsyncClient(base_url=self.base_url, timeout=10) as client:
            response = await client.get("/api/v3/ticker/24hr", params={"symbol": symbol.upper()})
            response.raise_for_status()
            payload = response.json()

        ticker = MarketTickerData(
            symbol=payload["symbol"],
            price=float(payload["lastPrice"]),
            change24h=float(payload["priceChangePercent"]),
            volume24h=float(payload["quoteVolume"]),
            source="binance.rest.ticker24hr",
        )
        return MarketEvent(
            event="market.ticker",
            exchange="binance",
            timestamp=now_ms(),
            data=model_to_dict(ticker),
        )

    async def fetch_funding(self, symbol: str) -> MarketEvent:
        import httpx

        async with httpx.AsyncClient(base_url=self.futures_base_url, timeout=10) as client:
            response = await client.get("/fapi/v1/premiumIndex", params={"symbol": symbol.upper()})
            response.raise_for_status()
            payload = response.json()

        return MarketEvent(
            event="market.funding",
            exchange="binance",
            timestamp=now_ms(),
            data={
                "symbol": payload["symbol"],
                "exchange": "binance",
                "fundingRate": float(payload.get("lastFundingRate") or 0.0),
                "nextFundingTime": int(payload.get("nextFundingTime") or 0),
                "source": "binance.futures.premiumIndex",
            },
        )

    async def fetch_open_interest(self, symbol: str) -> MarketEvent:
        import httpx

        async with httpx.AsyncClient(base_url=self.futures_base_url, timeout=10) as client:
            response = await client.get("/fapi/v1/openInterest", params={"symbol": symbol.upper()})
            response.raise_for_status()
            payload = response.json()

        return MarketEvent(
            event="market.open_interest",
            exchange="binance",
            timestamp=int(payload.get("time") or now_ms()),
            data={
                "symbol": payload["symbol"],
                "exchange": "binance",
                "openInterest": float(payload.get("openInterest") or 0.0),
                "changeRate": 0.0,
                "source": "binance.futures.openInterest",
            },
        )

    async def fetch_liquidations(self, symbol: str, limit: int = 20) -> list[MarketEvent]:
        import httpx

        async with httpx.AsyncClient(base_url=self.futures_base_url, timeout=10) as client:
            response = await client.get(
                "/fapi/v1/allForceOrders",
                params={"symbol": symbol.upper(), "limit": max(1, min(limit, 100))},
            )
            response.raise_for_status()
            payload = response.json()

        events = []
        for row in payload:
            price = float(row.get("avgPrice") or row.get("price") or 0.0)
            quantity = float(row.get("executedQty") or row.get("origQty") or 0.0)
            side = "long" if row.get("side") == "SELL" else "short"
            events.append(
                MarketEvent(
                    event="market.liquidation",
                    exchange="binance",
                    timestamp=int(row.get("time") or now_ms()),
                    data={
                        "symbol": row.get("symbol", symbol.upper()),
                        "exchange": "binance",
                        "side": side,
                        "price": price,
                        "quantity": quantity,
                        "value": price * quantity,
                        "source": "binance.futures.allForceOrders",
                    },
                )
            )
        return events
