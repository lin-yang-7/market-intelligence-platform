"""Validate real service dependencies and a bounded gateway load sample.

This command intentionally has no mock fallback. Run it only against a disposable
or approved environment with Redis, Kafka, ClickHouse, and the API gateway running.
"""

import argparse
import asyncio
import statistics
import time
import uuid


async def check_gateway(base_url: str, requests: int, concurrency: int) -> dict[str, float]:
    import httpx

    async with httpx.AsyncClient(timeout=5) as client:
        for suffix in ("/health", "/ready", "/metrics"):
            response = await client.get(f"{base_url.rstrip('/')}{suffix}")
            response.raise_for_status()
        semaphore = asyncio.Semaphore(concurrency)

        async def request_once() -> float:
            async with semaphore:
                started = time.perf_counter()
                response = await client.get(f"{base_url.rstrip('/')}/health")
                response.raise_for_status()
                return (time.perf_counter() - started) * 1000

        latencies = await asyncio.gather(*(request_once() for _ in range(requests)))
    return {"p50_ms": statistics.median(latencies), "p95_ms": percentile(latencies, 95)}


def percentile(values: list[float], percent: int) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((percent / 100) * (len(ordered) - 1)))
    return ordered[index]


async def check_redis(url: str) -> None:
    import redis.asyncio as redis

    key = f"mip:integration:{uuid.uuid4().hex}"
    client = redis.from_url(url, decode_responses=True)
    try:
        assert await client.ping()
        await client.set(key, "ok", ex=60)
        if await client.get(key) != "ok":
            raise RuntimeError("Redis probe value did not round-trip")
    finally:
        await client.delete(key)
        await client.aclose()


async def check_clickhouse(url: str, database: str, user: str, password: str) -> None:
    import httpx

    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.post(
            url.rstrip("/"),
            params={"database": database},
            content="SELECT 1 FORMAT JSONEachRow",
            auth=(user, password) if password else None,
        )
        response.raise_for_status()
    if response.text.strip() != '{"1":1}':
        raise RuntimeError("ClickHouse probe returned an unexpected result")


async def check_kafka(bootstrap_servers: str, topic: str) -> None:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

    marker = uuid.uuid4().hex
    producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=f"mip-integration-{marker}",
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )
    await producer.start()
    await consumer.start()
    try:
        await producer.send_and_wait(topic, marker.encode())
        records = await consumer.getmany(timeout_ms=10_000, max_records=10)
        received = any(
            record.value.decode() == marker
            for batch in records.values()
            for record in batch
        )
        if not received:
            raise RuntimeError("Kafka probe message was not consumed")
    finally:
        await consumer.stop()
        await producer.stop()


async def run(args: argparse.Namespace) -> None:
    await asyncio.gather(
        check_redis(args.redis_url),
        check_clickhouse(
            args.clickhouse_url,
            args.clickhouse_database,
            args.clickhouse_user,
            args.clickhouse_password,
        ),
        check_kafka(args.kafka_bootstrap_servers, args.kafka_topic),
    )
    load = await check_gateway(args.gateway_url, args.requests, args.concurrency)
    if load["p95_ms"] > args.max_p95_ms:
        raise RuntimeError(
            f"Gateway p95 {load['p95_ms']:.1f}ms exceeds {args.max_p95_ms:.1f}ms"
        )
    print(
        "ok: Redis, ClickHouse, Kafka, and gateway validated; "
        f"p50={load['p50_ms']:.1f}ms p95={load['p95_ms']:.1f}ms"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run real infrastructure integration checks")
    parser.add_argument("--gateway-url", default="http://localhost:8000")
    parser.add_argument("--redis-url", default="redis://localhost:6379/0")
    parser.add_argument("--clickhouse-url", default="http://localhost:8123")
    parser.add_argument("--clickhouse-database", default="market_intelligence")
    parser.add_argument("--clickhouse-user", default="default")
    parser.add_argument("--clickhouse-password", default="")
    parser.add_argument("--kafka-bootstrap-servers", default="localhost:9092")
    parser.add_argument("--kafka-topic", default="mip.integration.probe")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--max-p95-ms", type=float, default=500)
    args = parser.parse_args()
    if args.requests < 1 or args.concurrency < 1 or args.max_p95_ms <= 0:
        parser.error("requests, concurrency, and max-p95-ms must be positive")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
