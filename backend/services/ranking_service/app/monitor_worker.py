import asyncio
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
from mip_common.config import get_settings
from mip_common.responses import now_ms


@dataclass(frozen=True)
class MonitorWorkerConfig:
    ranking_service_url: str
    data_platform_url: str
    websocket_service_url: str
    notification_service_url: str
    exchange: str
    ranking_types: list[str]
    interval_seconds: int
    limit: int


class RankingMonitorPublisher(Protocol):
    async def publish_websocket(self, event: str, data: dict[str, Any]) -> None:
        ...

    async def publish_sse_notification(
        self,
        title: str,
        body: str,
        metadata: dict[str, str | int | float | bool | None],
    ) -> None:
        ...

    async def store_event(self, event: str, data: dict[str, Any], timestamp: int) -> None:
        ...


class HttpRankingMonitorPublisher:
    def __init__(
        self,
        client: httpx.AsyncClient,
        data_platform_url: str,
        websocket_service_url: str,
        notification_service_url: str,
    ) -> None:
        self.client = client
        self.data_platform_url = data_platform_url.rstrip("/")
        self.websocket_service_url = websocket_service_url.rstrip("/")
        self.notification_service_url = notification_service_url.rstrip("/")

    async def publish_websocket(self, event: str, data: dict[str, Any]) -> None:
        response = await self.client.post(
            f"{self.websocket_service_url}/v1/ws/publish",
            json={
                "event": event,
                "timestamp": now_ms(),
                "data": data,
            },
        )
        response.raise_for_status()

    async def store_event(self, event: str, data: dict[str, Any], timestamp: int) -> None:
        response = await self.client.post(
            f"{self.data_platform_url}/v1/data/ingest",
            json={
                "event_type": event,
                "timestamp": timestamp,
                "source": str(data.get("exchange") or "ranking-monitor"),
                "data": data,
            },
        )
        response.raise_for_status()

    async def publish_sse_notification(
        self,
        title: str,
        body: str,
        metadata: dict[str, str | int | float | bool | None],
    ) -> None:
        response = await self.client.post(
            f"{self.notification_service_url}/v1/notification/send",
            json={
                "channel": "sse",
                "userId": "default",
                "dedupeKey": metadata.get("dedupeKey"),
                "message": {
                    "title": title,
                    "body": body,
                    "severity": "info",
                    "metadata": metadata,
                },
            },
        )
        response.raise_for_status()


class RankingMonitorWorker:
    def __init__(
        self,
        client: httpx.AsyncClient,
        publisher: RankingMonitorPublisher,
        config: MonitorWorkerConfig,
    ) -> None:
        self.client = client
        self.publisher = publisher
        self.config = config

    async def run_once(self) -> list[dict[str, Any]]:
        snapshots = []
        for ranking_type in self.config.ranking_types:
            snapshot = await self.fetch_snapshot(ranking_type)
            snapshots.append(snapshot)
            await self.publish_snapshot(snapshot)
        return snapshots

    async def fetch_snapshot(self, ranking_type: str) -> dict[str, Any]:
        response = await self.client.post(
            f"{self.config.ranking_service_url.rstrip('/')}/v1/ranking/monitor/{ranking_type}",
            params={
                "exchange": self.config.exchange,
                "limit": self.config.limit,
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload["data"]

    async def publish_snapshot(self, snapshot: dict[str, Any]) -> None:
        changes = snapshot.get("changes") or {}
        changed_count = sum(len(changes.get(name) or []) for name in ("entered", "exited", "moved"))
        if changed_count == 0:
            return

        timestamp = int(snapshot.get("updatedAt") or now_ms())
        await self.publisher.publish_websocket("ranking.monitor.updated", snapshot)
        for event_key, websocket_event in (
            ("entered", "ranking.entered"),
            ("exited", "ranking.exited"),
            ("moved", "ranking.moved"),
        ):
            for item in changes.get(event_key) or []:
                event_data = {
                    "rankingType": snapshot["rankingType"],
                    "exchange": snapshot.get("exchange"),
                    "summary": snapshot.get("summary") or {},
                    **item,
                }
                await self.publisher.publish_websocket(websocket_event, event_data)
                try:
                    await self.publisher.store_event(websocket_event, event_data, timestamp)
                except Exception as exc:
                    print(f"ranking monitor store failed: {exc}")

        for strategy_event in changes.get("strategyEvents") or []:
            event_data = {
                "rankingType": snapshot["rankingType"],
                "exchange": snapshot.get("exchange"),
                "summary": snapshot.get("summary") or {},
                **strategy_event,
            }
            await self.publisher.publish_websocket("ranking.strategy", event_data)
            try:
                await self.publisher.store_event("ranking.strategy", event_data, timestamp)
            except Exception as exc:
                print(f"ranking strategy store failed: {exc}")

        await self.publisher.publish_sse_notification(
            title=f"{snapshot['rankingType']} monitor changed",
            body=self.notification_body(snapshot),
            metadata={
                "dedupeKey": self.dedupe_key(snapshot),
                "rankingType": snapshot["rankingType"],
                "exchange": snapshot.get("exchange"),
                "enteredCount": len(changes.get("entered") or []),
                "exitedCount": len(changes.get("exited") or []),
                "movedCount": len(changes.get("moved") or []),
                "strategyEventCount": len(changes.get("strategyEvents") or []),
            },
        )

    @staticmethod
    def dedupe_key(snapshot: dict[str, Any]) -> str:
        changes = snapshot.get("changes") or {}
        parts = [
            snapshot["rankingType"],
            str(snapshot.get("exchange") or ""),
            ",".join(item["symbol"] for item in changes.get("entered") or []),
            ",".join(item["symbol"] for item in changes.get("exited") or []),
            ",".join(item["symbol"] for item in changes.get("moved") or []),
            ",".join(item["event"] for item in changes.get("strategyEvents") or []),
        ]
        return "ranking-monitor:" + ":".join(parts)

    @staticmethod
    def notification_body(snapshot: dict[str, Any]) -> str:
        changes = snapshot.get("changes") or {}
        return (
            f"active={len(snapshot.get('active') or [])}, "
            f"entered={len(changes.get('entered') or [])}, "
            f"exited={len(changes.get('exited') or [])}, "
            f"moved={len(changes.get('moved') or [])}, "
            f"strategy={len(changes.get('strategyEvents') or [])}"
        )

    async def run_forever(self) -> None:
        while True:
            try:
                await self.run_once()
            except Exception as exc:
                print(f"ranking monitor failed: {exc}")
            await asyncio.sleep(max(5, self.config.interval_seconds))


def build_config() -> MonitorWorkerConfig:
    settings = get_settings()
    return MonitorWorkerConfig(
        ranking_service_url=settings.ranking_service_url,
        data_platform_url=settings.data_platform_url,
        websocket_service_url=settings.websocket_service_url,
        notification_service_url=settings.notification_service_url,
        exchange=settings.ranking_monitor_exchange,
        ranking_types=[
            item.strip()
            for item in settings.ranking_monitor_types.split(",")
            if item.strip()
        ],
        interval_seconds=settings.ranking_monitor_interval_seconds,
        limit=settings.ranking_monitor_limit,
    )


async def async_main() -> None:
    settings = get_settings()
    if not settings.ranking_monitor_enabled:
        print("ranking monitor disabled")
        return
    config = build_config()
    async with httpx.AsyncClient(timeout=10) as client:
        publisher = HttpRankingMonitorPublisher(
            client,
            data_platform_url=config.data_platform_url,
            websocket_service_url=config.websocket_service_url,
            notification_service_url=config.notification_service_url,
        )
        worker = RankingMonitorWorker(client, publisher, config)
        await worker.run_forever()


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
