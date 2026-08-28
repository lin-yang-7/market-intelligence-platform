from datetime import UTC, datetime
from typing import Any, Protocol


class ClickHouseClient(Protocol):
    async def insert(self, table: str, rows: list[dict[str, Any]]) -> None:
        ...

    async def select(self, query: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        ...


def ms_to_datetime_text(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).strftime("%Y-%m-%d %H:%M:%S")


def datetime_text_to_ms(value: str | datetime) -> int:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return int(value.timestamp() * 1000)
    parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    return int(parsed.timestamp() * 1000)


class HttpClickHouseClient:
    def __init__(
        self,
        base_url: str,
        database: str,
        user: str = "default",
        password: str = "",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.database = database
        self.user = user
        self.password = password

    async def insert(self, table: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        import httpx

        columns = list(rows[0].keys())
        values = "\n".join(
            "\t".join(str(row.get(column, "")) for column in columns)
            for row in rows
        )
        query = f"INSERT INTO {self.database}.{table} ({', '.join(columns)}) FORMAT TabSeparated"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                self.base_url,
                params={"query": query},
                content=values,
                auth=(self.user, self.password) if self.password else None,
            )
            response.raise_for_status()

    async def select(self, query: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        import httpx

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                self.base_url,
                params={**parameters, "database": self.database},
                content=query + " FORMAT JSONEachRow",
                auth=(self.user, self.password) if self.password else None,
            )
            response.raise_for_status()
        rows = []
        for line in response.text.splitlines():
            if not line.strip():
                continue
            import json

            rows.append(json.loads(line))
        return rows

