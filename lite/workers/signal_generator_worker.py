"""Lite internal bridge that turns calculated rankings into durable signal events.

It has no host port and is intentionally kept out of the public gateway.  The
worker makes the ranking → signal → storage/push portion of the Lite pipeline
automatic rather than relying on a client to invoke it.
"""

import asyncio
import os
from typing import Any

import httpx
from mip_common.responses import now_ms

RANKING_TYPES = ("overall", "longInflow", "momentum", "volume")


async def _post(client: httpx.AsyncClient, url: str, payload: dict[str, Any]) -> None:
    response = await client.post(url, json=payload)
    response.raise_for_status()


async def run_once(client: httpx.AsyncClient) -> int:
    ranking_url = os.getenv("RANKING_SERVICE_URL", "http://ranking-service:8004").rstrip("/")
    signal_url = os.getenv("SIGNAL_SERVICE_URL", "http://signal-service:8005").rstrip("/")
    data_url = os.getenv("DATA_PLATFORM_URL", "http://data-platform:8011").rstrip("/")
    websocket_url = os.getenv("WEBSOCKET_SERVICE_URL", "http://websocket-service:8008").rstrip("/")
    notification_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8012").rstrip("/")
    alert_url = os.getenv("ALERT_SERVICE_URL", "http://alert-service:8006").rstrip("/")
    token = os.environ["INTERNAL_SERVICE_TOKEN"]
    total = 0
    for ranking_type in RANKING_TYPES:
        response = await client.get(
            f"{ranking_url}/v1/ranking/{ranking_type}",
            params={"exchange": "binance", "limit": 50},
        )
        if response.status_code == 400:
            continue  # No feature data yet during initial collector warm-up.
        response.raise_for_status()
        ranking = response.json()["data"]
        timestamp = now_ms()
        for item in ranking:
            await _post(client, f"{data_url}/v1/data/ingest", {
                "event_type": "ranking.updated", "timestamp": timestamp,
                "source": item["exchange"],
                "data": {"type": ranking_type, **item},
            })
        generated = await client.post(
            f"{signal_url}/internal/signals/generate",
            headers={"X-Internal-Service-Token": token},
            json={"rankingType": ranking_type, "ranking": ranking, "minScore": 70},
        )
        generated.raise_for_status()
        signals = generated.json()["data"]
        for signal in signals:
            event = {"event": "signal.created", "timestamp": signal["timestamp"], "data": signal}
            await _post(client, f"{data_url}/v1/data/ingest", {
                "event_type": "signal.created", "timestamp": signal["timestamp"],
                "source": signal["exchange"], "data": signal,
            })
            await _post(client, f"{websocket_url}/v1/ws/publish", event)
            await _post(
                client,
                f"{alert_url}/internal/alerts/evaluate",
                signal,
            )
        if signals:
            await _post(client, f"{notification_url}/v1/notification/send", {
                "channel": "console", "userId": "system",
                "dedupeKey": f"signal:{ranking_type}:{timestamp // 60000}",
                "message": {
                    "title": f"{ranking_type} signals updated",
                    "body": f"Generated {len(signals)} signals.", "severity": "info",
                    "metadata": {"rankingType": ranking_type, "signalCount": len(signals)},
                },
            })
        total += len(signals)
    return total


async def main() -> None:
    interval = max(10, int(os.getenv("SIGNAL_GENERATOR_INTERVAL_SECONDS", "60")))
    async with httpx.AsyncClient(timeout=15) as client:
        while True:
            try:
                await run_once(client)
            except Exception as exc:
                print(f"signal generator failed: {exc}")
            await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(main())
