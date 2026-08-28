class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    async def get(self, key: str):
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.values[key] = value
        if ex is not None:
            self.ttls[key] = ex


class FakeKafkaProducer:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False
        self.sent: list[tuple[str, bytes]] = []

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    async def send_and_wait(self, topic: str, payload: bytes) -> None:
        self.sent.append((topic, payload))


class FakeClickHouseClient:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict]] = {}
        self.select_calls: list[tuple[str, dict]] = []

    async def insert(self, table: str, rows: list[dict]) -> None:
        self.tables.setdefault(table, []).extend(rows)

    async def select(self, query: str, parameters: dict) -> list[dict]:
        self.select_calls.append((query, parameters))
        if "market_kline" in query:
            rows = self.tables.get("market_kline", [])
            return [
                row
                for row in rows
                if row["symbol"] == parameters["symbol"]
                and row["interval"] == parameters["interval"]
            ][: parameters["limit"]]
        if "feature_history" in query:
            rows = self.tables.get("feature_history", [])
            return [
                row
                for row in rows
                if row["symbol"] == parameters["symbol"]
                and row["feature_name"] == parameters["feature"]
            ][: parameters["limit"]]
        if "signal_history" in query:
            rows = self.tables.get("signal_history", [])
            return [row for row in rows if row["symbol"] == parameters["symbol"]][
                : parameters["limit"]
            ]
        return []
